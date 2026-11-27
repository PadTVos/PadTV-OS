use crate::{apk, dex, manager::Manager};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{
    env, fs,
    path::{Path, PathBuf},
    process::{Command, Stdio},
};

struct PlaybackBroker {
    child: std::process::Child,
    directory: tempfile::TempDir,
}
impl PlaybackBroker {
    fn start(runtime: &Path, log: &Path) -> Result<Self> {
        let directory = tempfile::tempdir()?;
        let socket = directory.path().join("playback.sock");
        let mut cmd = Command::new("/usr/bin/python3");
        cmd.env_clear()
            .env("PATH", "/usr/bin:/bin")
            .env("LANG", "C.UTF-8");
        if let Some(xdg) = env::var_os("XDG_RUNTIME_DIR") {
            cmd.env("XDG_RUNTIME_DIR", &xdg);
            cmd.env(
                "PULSE_SERVER",
                format!("unix:{}/pulse/native", PathBuf::from(xdg).display()),
            );
        }
        let child = cmd
            .arg(runtime.join("audio_broker.py"))
            .arg(&socket)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(fs::File::create(log)?)
            .spawn()
            .context("Playback broker could not start")?;
        let mut broker = Self { child, directory };
        for _ in 0..100 {
            if socket.exists() {
                return Ok(broker);
            }
            ensure!(
                broker.child.try_wait()?.is_none(),
                "Playback broker exited before readiness"
            );
            std::thread::sleep(std::time::Duration::from_millis(10));
        }
        anyhow::bail!("Playback broker readiness timeout")
    }
    fn socket(&self) -> PathBuf {
        self.directory.path().join("playback.sock")
    }
}
impl Drop for PlaybackBroker {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

pub(crate) fn share() -> PathBuf {
    env::var_os("PADBRIDGE_RUNTIME_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/usr/lib/padbridge"))
}

pub(crate) fn sandbox(network: bool) -> Result<Command> {
    ensure!(
        cfg!(target_os = "linux"),
        "PadBridge execution requires Linux; Windows supports PadTV preview only"
    );
    let mut cmd = Command::new("/usr/bin/bwrap");
    cmd.env_clear();
    cmd.args([
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--cap-drop",
        "ALL",
        "--clearenv",
    ]);
    if network {
        cmd.arg("--share-net");
    }
    for path in ["/usr", "/lib", "/lib64", "/bin"] {
        if Path::new(path).exists() {
            cmd.args(["--ro-bind", path, path]);
        }
    }
    cmd.args([
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/etc",
        "--dir",
        "/run",
        "--dir",
        "/run/padbridge",
    ]);
    for path in [
        "/etc/ssl/certs",
        "/etc/fonts",
        "/etc/alternatives",
        "/etc/java-21-openjdk",
        "/etc/ld.so.cache",
        "/etc/resolv.conf",
        "/etc/nsswitch.conf",
    ] {
        if Path::new(path).exists() {
            cmd.args(["--ro-bind", path, path]);
        }
    }
    cmd.args([
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--setenv",
        "HOME",
        "/data",
        "--setenv",
        "XDG_RUNTIME_DIR",
        "/run/padbridge",
    ]);
    Ok(cmd)
}

pub(crate) fn translate(version: &Path, runtime: &Path) -> Result<()> {
    let cache_version = format!(
        "{}:{}:{}:{}:{}:{}",
        env!("CARGO_PKG_VERSION"),
        apk::digest(&runtime.join("translate.py"))?,
        apk::digest(&runtime.join("resources.py"))?,
        apk::digest(&runtime.join("framework.jar"))?,
        apk::digest(&runtime.join("dex_fixes.py"))?,
        apk::digest(&runtime.join("constructor-repair.jar"))?
    );
    if version.join("classes.jar").exists()
        && fs::read_to_string(version.join("cache-version")).unwrap_or_default() == cache_version
    {
        return Ok(());
    }
    let stage = tempfile::tempdir_in(version)?;
    let mut cmd = sandbox(false)?;
    cmd.arg("--ro-bind").arg(runtime).arg("/runtime");
    cmd.arg("--ro-bind").arg(version).arg("/input");
    cmd.arg("--bind").arg(stage.path()).arg("/output");
    cmd.args([
        "--",
        "/usr/bin/timeout",
        "--kill-after=3",
        "90",
        "/usr/bin/python3",
        "/runtime/translate.py",
        "/input",
        "/output/classes.jar",
    ]);
    let output = cmd
        .output()
        .context("Mandatory bubblewrap sandbox is unavailable")?;
    ensure!(
        output.status.success(),
        "DEX translation / sandbox failed: {}",
        String::from_utf8_lossy(&output.stderr)
            .chars()
            .take(3000)
            .collect::<String>()
    );
    ensure!(
        stage
            .path()
            .join("classes.jar")
            .metadata()
            .context("DEX translator did not produce classes.jar")?
            .len()
            <= 256 * 1024 * 1024,
        "Translated JAR exceeds limit"
    );
    fs::rename(
        stage.path().join("classes.jar"),
        version.join("classes.jar"),
    )?;
    fs::write(
        version.join("classes.jar.sha256"),
        apk::digest(&version.join("classes.jar"))?,
    )?;
    fs::write(version.join("cache-version"), cache_version)?;
    Ok(())
}

pub fn run(
    manager: &Manager,
    package: &str,
    headless: bool,
    restart: bool,
    backend_id: &str,
) -> Result<Value> {
    manager.app_dir(package)?;
    let _guard = manager.operation_lock(package)?;
    let mut trace = crate::startup::Trace::new(
        manager
            .root
            .join("logs")
            .join(format!("{package}.startup.json")),
        package,
        backend_id,
    );
    trace.phase("backend.select")?;
    let mut result = run_inner(manager, package, headless, restart, backend_id, &mut trace);
    trace.finish(&result)?;
    if let Ok(ref mut value) = result {
        value["startup_trace"] = json!(trace.path());
    }
    result
}
fn run_inner(
    manager: &Manager,
    package: &str,
    headless: bool,
    restart: bool,
    backend_id: &str,
    trace: &mut crate::startup::Trace,
) -> Result<Value> {
    let backend = crate::backends::select(backend_id)?;
    trace.phase("package.integrity")?;
    let app = manager.get(package)?;
    trace.identity(json!({"sha256":app.sha256,"signers":app.signers,"splits":app.splits}))?;
    let grants = manager.grants(package)?;
    let version = manager.app_dir(package)?.join(app.storage_id());
    ensure!(
        apk::digest(&version.join("original.apk"))? == app.sha256,
        "Installed APK integrity mismatch"
    );
    ensure!(!app.activity.is_empty(), "No launchable Activity found");
    let mut sources = vec![version.join("original.apk")];
    for split in &app.splits {
        ensure!(
            !split.name.contains('/') && !split.name.contains('\\') && !split.name.contains(".."),
            "Unsafe installed split name"
        );
        let path = version.join("splits").join(format!("{}.apk", split.name));
        ensure!(
            apk::digest(&path)? == split.sha256,
            "Installed split integrity mismatch"
        );
        sources.push(path);
    }
    trace.phase("dex.inspect")?;
    let diagnostic = dex::diagnose_set(&sources)?;
    ensure!(
        diagnostic["dex_errors"]
            .as_array()
            .map(|v| v.is_empty())
            .unwrap_or(false),
        "Unsupported APK: {diagnostic}"
    );
    let runtime = share()
        .canonicalize()
        .context("PadBridge runtime is not installed")?;
    trace.phase("native.stage")?;
    let native = crate::native_elf::stage(&sources, &version)?;
    trace.phase("dex.prepare")?;
    backend.prepare(&version, &runtime)?;
    ensure!(
        apk::digest(&version.join(backend.artifact()))?
            == fs::read_to_string(version.join(format!("{}.sha256", backend.artifact())))?,
        "Runtime artifact integrity mismatch"
    );
    manager.unlock()?; // Other packages remain manageable while this one is running.
    let data = manager.root.join("data").join(package).canonicalize()?;
    ensure!(
        data.parent() == Some(manager.root.join("data").as_path()),
        "Application data escapes private directory"
    );
    let network = grants
        .iter()
        .any(|p| p == "android.permission.INTERNET" && app.permissions.contains(p));
    let certificates = crate::certificates::current(manager, package)?;
    let log_path = manager.root.join("logs").join(format!("{package}.log"));
    let mut attempts = 0;
    loop {
        attempts += 1;
        trace.phase("sandbox.prepare")?;
        let mut cmd = sandbox(network)?;
        cmd.arg("--ro-bind").arg(&runtime).arg("/runtime");
        cmd.arg("--ro-bind").arg(&version).arg("/app");
        cmd.arg("--bind").arg(&data).arg("/data");
        backend.configure(&mut cmd)?;
        if let Some(ref path) = certificates {
            cmd.arg("--ro-bind").arg(path).arg("/certificates");
            cmd.args(["--setenv","JAVA_TOOL_OPTIONS","-Djavax.net.ssl.trustStore=/certificates/cacerts -Djavax.net.ssl.trustStorePassword=changeit","--setenv","PADBRIDGE_CA_BUNDLE","/certificates/ca-bundle.pem"]);
        }
        cmd.arg("--ro-bind").arg(native.path()).arg("/native");
        cmd.args(["--setenv", "LD_LIBRARY_PATH", "/native"]);
        // A bounded playback-only protocol; the APK cannot connect to host audio capture.
        let broker = PlaybackBroker::start(&runtime, &log_path.with_extension("audio.log"))?;
        cmd.arg("--ro-bind")
            .arg(broker.socket())
            .arg("/run/padbridge/playback.sock");
        cmd.args([
            "--setenv",
            "PADBRIDGE_AUDIO_SOCKET",
            "/run/padbridge/playback.sock",
        ]);
        if headless {
            cmd.args(["--setenv", "PADBRIDGE_HEADLESS", "1"]);
        }
        if !headless {
            let xdg = PathBuf::from(env::var_os("XDG_RUNTIME_DIR").context("No Wayland session")?);
            let display = env::var("WAYLAND_DISPLAY").unwrap_or_else(|_| "wayland-0".into());
            ensure!(
                !display.contains('/') && display != "." && display != "..",
                "Invalid Wayland socket name"
            );
            let socket = xdg.join(&display);
            ensure!(socket.exists(), "Wayland compositor is unavailable");
            cmd.arg("--ro-bind")
                .arg(socket)
                .arg(format!("/run/padbridge/{display}"));
            cmd.args([
                "--setenv",
                "WAYLAND_DISPLAY",
                &display,
                "--setenv",
                "SDL_VIDEODRIVER",
                "wayland",
            ]);
            cmd.args([
                "--setenv",
                "SDL_VIDEO_WAYLAND_WMCLASS",
                &format!("padbridge.{package}"),
            ]);
        }
        let log = fs::File::create(&log_path)?;
        crate::manager::atomic_json(
            &log_path.with_extension("identity.json"),
            &json!({
                "apk_storage_id": app.storage_id(), "backend": backend.id(),
                "padbridge_version": env!("CARGO_PKG_VERSION"),
                "framework_sha256": apk::digest(&runtime.join(backend.framework()))?
            }),
        )?;
        cmd.stdout(Stdio::from(log.try_clone()?))
            .stderr(Stdio::from(log));
        cmd.args(["--chdir", "/data", "--"]).args(backend.command(
            &app.activity,
            &app.package,
            headless,
        )?);
        trace.phase("sandbox.execute")?;
        let status = cmd
            .status()
            .context("Mandatory bubblewrap sandbox could not start")?;
        trace.phase("process.exit")?;
        let tail = fs::read_to_string(&log_path).unwrap_or_default();
        let tail = tail
            .chars()
            .rev()
            .take(5000)
            .collect::<String>()
            .chars()
            .rev()
            .collect::<String>();
        if status.success() {
            return Ok(
                json!({"ok":true,"exit_code":0,"attempts":attempts,"log":log_path,"output":tail}),
            );
        }
        if !restart || attempts >= 2 || status.code() == Some(78) {
            return Ok(
                json!({"ok":false,"exit_code":status.code(),"attempts":attempts,"log":log_path,
                "error":"Application or sandbox failed; no unconfined fallback was attempted","output":tail}),
            );
        }
    }
}
