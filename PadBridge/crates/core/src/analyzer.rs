use crate::{bundles::Bundle, manager::Manager, runtime};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{fs, path::PathBuf};

pub fn analyze(manager: &Manager, paths: &[PathBuf], html: Option<&str>) -> Result<Value> {
    let bundle = Bundle::load(paths, &manager.root)?;
    let runtime_dir = runtime::share().canonicalize()?;
    let mut cmd = runtime::sandbox(false)?;
    cmd.arg("--ro-bind").arg(runtime_dir).arg("/runtime");
    let mut inputs = vec![];
    for (i, path) in bundle.paths.iter().enumerate() {
        let target = format!("/input{i}.apk");
        cmd.arg("--ro-bind").arg(path.canonicalize()?).arg(&target);
        inputs.push(target);
    }
    cmd.args([
        "--",
        "/usr/bin/timeout",
        "--kill-after=3",
        "90",
        "/usr/bin/python3",
        "/runtime/analyze.py",
    ])
    .args(inputs);
    let output = cmd
        .output()
        .context("Mandatory analyzer sandbox unavailable")?;
    ensure!(
        output.status.success(),
        "Analyzer failed: {} {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    let static_report: Value = serde_json::from_slice(&output.stdout)?;
    ensure!(static_report["ok"] == true, "Analyzer rejected input");
    // A historical log is evidence for an installed build only, not arbitrary APKs.
    let installed = manager.get(&bundle.app.package).ok();
    let identity_path = manager
        .root
        .join("logs")
        .join(format!("{}.identity.json", bundle.app.package));
    let identity: Value = fs::read(&identity_path)
        .ok()
        .and_then(|b| serde_json::from_slice(&b).ok())
        .unwrap_or(Value::Null);
    let matching = installed.as_ref().map(|a| a.storage_id()) == Some(bundle.app.storage_id())
        && identity["apk_storage_id"].as_str() == Some(bundle.app.storage_id());
    let log = if matching {
        fs::read_to_string(
            manager
                .root
                .join("logs")
                .join(format!("{}.log", bundle.app.package)),
        )
        .unwrap_or_default()
    } else {
        String::new()
    };
    let observed: Vec<_> = log
        .lines()
        .filter(|l| {
            l.contains("Error") || l.contains("Exception") || l.contains("PADBRIDGE_UNSUPPORTED")
        })
        .take(80)
        .map(|s| s.chars().take(2000).collect::<String>())
        .collect();
    let report = json!({"ok":true,"analyzer_version":"0.3.0","app":bundle.app,"static":static_report,
        "native":crate::dex::diagnose_set(&bundle.paths)?,"observed_runtime_errors":observed,
        "runtime_log_matches_installed_build":matching,"observed_runtime_identity":if matching {identity}else{Value::Null},"tested_playback":false});
    if let Some(path) = html {
        let data = serde_json::to_string_pretty(&report)?
            .replace('&', "&amp;")
            .replace('<', "&lt;")
            .replace('>', "&gt;");
        fs::write(path,format!("<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width'><title>PadBridge Compatibility Analyzer</title><style>body{{background:#111827;color:#e5e7eb;font:16px system-ui;margin:3rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}h1{{color:#c4b5fd}}</style><h1>PadBridge Compatibility Analyzer</h1><p>Static references are potential requirements. Observed runtime errors are separate. This report does not certify application compatibility or DRM.</p><pre>{data}</pre></html>"))?;
    }
    Ok(report)
}
