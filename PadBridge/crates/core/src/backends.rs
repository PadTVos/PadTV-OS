//! Runtime selection is explicit. An unavailable backend never falls back silently.
use anyhow::{bail, ensure, Context, Result};
use serde_json::{json, Value};
use std::{
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

pub trait Backend {
    fn id(&self) -> &'static str;
    fn available(&self) -> bool;
    fn details(&self) -> Value;
    fn prepare(&self, version: &Path, runtime: &Path) -> Result<()>;
    fn configure(&self, _: &mut Command) -> Result<()> {
        Ok(())
    }
    fn artifact(&self) -> &'static str {
        "classes.jar"
    }
    fn framework(&self) -> &'static str {
        "framework.jar"
    }
    /// Arguments are executed inside the common mandatory sandbox, never a shell.
    fn command(&self, activity: &str, package: &str, headless: bool) -> Result<Vec<String>>;
}
pub struct Enjarify;
impl Backend for Enjarify {
    fn prepare(&self, version: &Path, runtime: &Path) -> Result<()> {
        crate::runtime::translate(version, runtime)
    }
    fn command(&self, activity: &str, package: &str, headless: bool) -> Result<Vec<String>> {
        Ok([
            "/usr/bin/java",
            "-Xmx384m",
            "-XX:ActiveProcessorCount=2",
            "-Djava.library.path=/runtime:/native:/usr/lib/x86_64-linux-gnu/jni",
            "-cp",
            "/runtime/framework.jar:/app/classes.jar:/usr/share/java/sqlite-jdbc.jar",
            "org.padtv.bridge.Host",
            activity,
            package,
            if headless { "headless" } else { "wayland" },
        ]
        .iter()
        .map(|s| s.to_string())
        .collect())
    }
    fn id(&self) -> &'static str {
        "enjarify-openjdk"
    }
    fn available(&self) -> bool {
        cfg!(target_os = "linux")
    }
    fn details(&self) -> Value {
        json!({"id":self.id(),"available":self.available(),"experimental":true,
        "dex_metadata_versions":["035","037","038","039","040"],
        "execution":"Strict translation; unsupported opcodes fail, never partial bytecode",
        "requires":["bubblewrap","OpenJDK 21","Enjarify"]})
    }
}
pub struct Art;
pub fn art_root() -> PathBuf {
    env::var_os("PADBRIDGE_ART_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            env::var_os("XDG_DATA_HOME")
                .map(PathBuf::from)
                .unwrap_or_else(|| {
                    PathBuf::from(env::var_os("HOME").unwrap_or_default()).join(".local/share")
                })
                .join("padbridge-runtimes/art-16.0.0")
        })
}
impl Backend for Art {
    fn artifact(&self) -> &'static str {
        "art-resources.jar"
    }
    fn framework(&self) -> &'static str {
        "framework-art.jar"
    }
    fn configure(&self, command: &mut Command) -> Result<()> {
        let root = art_root().canonicalize().context("ART is not installed")?;
        command.arg("--ro-bind").arg(&root).arg("/art");
        command.arg("--ro-bind").arg(root.join("boot")).arg("/boot");
        Ok(())
    }
    fn prepare(&self, version: &Path, runtime: &Path) -> Result<()> {
        let verify = Command::new("/usr/bin/python3")
            .arg(runtime.join("art_runtime.py"))
            .arg("verify")
            .arg(art_root())
            .output()?;
        ensure!(
            verify.status.success(),
            "ART integrity verification failed: {}",
            String::from_utf8_lossy(&verify.stdout)
        );
        ensure!(
            runtime.join(self.framework()).is_file(),
            "ART DEX framework is not built"
        );
        let stage = tempfile::tempdir_in(version)?;
        let mut command = crate::runtime::sandbox(false)?;
        command
            .arg("--ro-bind")
            .arg(runtime)
            .arg("/runtime")
            .arg("--ro-bind")
            .arg(version)
            .arg("/input")
            .arg("--bind")
            .arg(stage.path())
            .arg("/output")
            .args([
                "--",
                "/usr/bin/timeout",
                "--kill-after=3",
                "90",
                "/usr/bin/python3",
                "/runtime/art_runtime.py",
                "prepare",
                "/input",
                "/output/art-resources.jar",
            ]);
        let output = command.output()?;
        ensure!(
            output.status.success(),
            "ART resources preparation failed: {} {}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
        let artifact = version.join(self.artifact());
        fs::rename(stage.path().join(self.artifact()), &artifact)?;
        fs::write(
            version.join(format!("{}.sha256", self.artifact())),
            crate::apk::digest(&artifact)?,
        )?;
        Ok(())
    }
    fn command(&self, activity: &str, package: &str, headless: bool) -> Result<Vec<String>> {
        Ok([
            "/usr/bin/python3",
            "/runtime/art_runtime.py",
            "run",
            activity,
            package,
            if headless { "headless" } else { "wayland" },
        ]
        .iter()
        .map(|s| s.to_string())
        .collect())
    }
    fn id(&self) -> &'static str {
        "aosp-art"
    }
    fn available(&self) -> bool {
        cfg!(target_os = "linux") && art_root().join("padbridge-art.json").is_file()
    }
    fn details(&self) -> Value {
        json!({"id":self.id(),"available":self.available(),"experimental":true,
        "execution":"Original DEX in matched AOSP ART/libcore; full Android framework compatibility is incomplete",
        "requires":["bubblewrap","pinned Linux x86-64 ART host bundle","verified boot image"],
        "setup":"padbridge setup-art", "root":art_root(),
        "reason":if self.available(){"Verified installation present; file integrity is rechecked before each run"}else{"Run setup-art to download and verify the pinned runtime; Enjarify remains available"}})
    }
}
pub fn list() -> Value {
    json!([Enjarify.details(), Art.details()])
}
pub fn select(id: &str) -> Result<Box<dyn Backend>> {
    let backend: Box<dyn Backend> = match id {
        "enjarify-openjdk" => Box::new(Enjarify),
        "aosp-art" => Box::new(Art),
        _ => bail!("Unknown runtime backend: {id}"),
    };
    if !backend.available() {
        bail!("Runtime backend is unavailable: {}", backend.details());
    }
    Ok(backend)
}
#[cfg(test)]
mod tests {
    #[test]
    fn art_is_not_faked() {
        assert!(super::select("aosp-art").is_err());
        assert!(super::select("anything").is_err());
    }
}
