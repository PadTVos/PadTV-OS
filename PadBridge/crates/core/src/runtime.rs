use crate::{apk, dex, manager::Manager};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{
    env, fs,
    path::{Path, PathBuf},
    process::{Command, Stdio},
};

fn share() -> PathBuf {
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
        "{}:{}:{}:{}",
        env!("CARGO_PKG_VERSION"),
        apk::digest(&runtime.join("translate.py"))?,
        apk::digest(&runtime.join("resources.py"))?,
        apk::digest(&runtime.join("framework.jar"))?
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
        stage.path().join("classes.jar").metadata()?.len() <= 256 * 1024 * 1024,
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
    let backend = crate::backends::select(backend_id)?;
    let _guard = manager.operation_lock(package)?;
    let app = manager.get(package)?;
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
    let diagnostic = dex::diagnose_set(&sources)?;
    ensure!(
        diagnostic["dex_errors"]
            .as_array()
            .map(|v| v.is_empty())
            .unwrap_or(false)
            && diagnostic["native_abi_supported"] == true,
        "Unsupported APK: {diagnostic}"
    );
    let runtime = share()
        .canonicalize()
        .context("PadBridge runtime is not installed")?;
    backend.prepare(&version, &runtime)?;
    ensure!(
        apk::digest(&version.join("classes.jar"))?
            == fs::read_to_string(version.join("classes.jar.sha256"))?,
        "Translated cache integrity mismatch"
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
    let log_path = manager.root.join("logs").join(format!("{package}.log"));
    let mut attempts = 0;
    loop {
        attempts += 1;
        let mut cmd = sandbox(network)?;
        cmd.arg("--ro-bind").arg(&runtime).arg("/runtime");
        cmd.arg("--ro-bind").arg(&version).arg("/app");
        cmd.arg("--bind").arg(&data).arg("/data");
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
        cmd.stdout(Stdio::from(log.try_clone()?))
            .stderr(Stdio::from(log));
        cmd.args(["--chdir", "/data", "--"]).args(backend.command(
            &app.activity,
            &app.package,
            headless,
        )?);
        let status = cmd
            .status()
            .context("Mandatory bubblewrap sandbox could not start")?;
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
