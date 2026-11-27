//! Supervisor-owned start stages, separate from untrusted application output.
use anyhow::Result;
use serde_json::{json, Value};
use std::{path::PathBuf, time::Instant};
pub struct Trace {
    path: PathBuf,
    started: Instant,
    entries: Vec<Value>,
    package: String,
    backend: String,
    identity: Value,
    application: Value,
    exit_code: Value,
}
impl Trace {
    pub fn new(path: PathBuf, package: &str, backend: &str) -> Self {
        Self {
            path,
            started: Instant::now(),
            entries: vec![],
            package: package.into(),
            backend: backend.into(),
            identity: Value::Null,
            application: Value::Null,
            exit_code: Value::Null,
        }
    }
    fn save(&self, status: &str, error: Option<String>) -> Result<()> {
        crate::manager::atomic_json(
            &self.path,
            &json!({"schema":1,"package":self.package,"backend":self.backend,
            "version":env!("CARGO_PKG_VERSION"),"status":status,"error":error,"stages":self.entries,
            "application_output_is_untrusted":true,"package_identity":self.identity,"application_reported":self.application,"process_exit_code":self.exit_code}),
        )
    }
    pub fn identity(&mut self, value: Value) -> Result<()> {
        self.identity = value;
        self.save("running", None)
    }
    pub fn phase(&mut self, name: &str) -> Result<()> {
        self.entries
            .push(json!({"stage":name,"elapsed_ms":self.started.elapsed().as_millis()}));
        self.save("running", None)
    }
    pub fn finish(&mut self, result: &Result<Value>) -> Result<()> {
        if let Ok(value) = result {
            self.exit_code = value.get("exit_code").cloned().unwrap_or(Value::Null);
            let output = value.get("output").and_then(Value::as_str).unwrap_or("");
            let phases: Vec<&str> = output
                .lines()
                .filter_map(|l| l.strip_prefix("PADBRIDGE_PHASE="))
                .filter(|p| p.len() <= 80)
                .take(64)
                .collect();
            let failed = output
                .lines()
                .filter_map(|l| l.strip_prefix("PADBRIDGE_FAILED_PHASE="))
                .find(|p| p.len() <= 80);
            self.application =
                json!({"trusted":false,"phases_from_output_tail":phases,"failed_phase":failed});
        }
        let (ok, error) = match result {
            Ok(v) => (
                v["ok"].as_bool() == Some(true),
                v.get("error").and_then(Value::as_str).map(str::to_owned),
            ),
            Err(e) => (false, Some(format!("{e:#}"))),
        };
        self.save(if ok { "exited_successfully" } else { "failed" }, error)
    }
    pub fn path(&self) -> &std::path::Path {
        &self.path
    }
}
