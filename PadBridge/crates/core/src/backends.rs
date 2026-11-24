//! Runtime selection is explicit. An unavailable backend never falls back silently.
use anyhow::{bail, Result};
use serde_json::{json, Value};
use std::path::Path;

pub trait Backend {
    fn id(&self) -> &'static str;
    fn available(&self) -> bool;
    fn details(&self) -> Value;
    fn prepare(&self, version: &Path, runtime: &Path) -> Result<()>;
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
impl Backend for Art {
    fn prepare(&self, _: &Path, _: &Path) -> Result<()> {
        bail!("AOSP ART has not been built or validated")
    }
    fn command(&self, _: &str, _: &str, _: bool) -> Result<Vec<String>> {
        bail!("AOSP ART execution is unavailable")
    }
    fn id(&self) -> &'static str {
        "aosp-art"
    }
    fn available(&self) -> bool {
        false
    }
    fn details(&self) -> Value {
        json!({"id":self.id(),"available":false,"experimental":true,
        "reason":"Host ART, matching boot image/libcore, JNI ABI and sandbox integration are not built or validated"})
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
