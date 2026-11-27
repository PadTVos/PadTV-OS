//! Explicit per-package certificate trust, read-only in the application sandbox.
use crate::{
    apk,
    manager::{self, Manager},
    runtime,
};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{fs, path::PathBuf};

pub fn current(manager: &Manager, package: &str) -> Result<Option<PathBuf>> {
    ensure!(apk::valid_package(package), "Invalid package");
    let root = manager.root.join("certificates").join(package);
    let pointer = root.join("current.json");
    if !pointer.exists() {
        return Ok(None);
    }
    let v: Value = serde_json::from_slice(&fs::read(pointer)?)?;
    let name = v["generation"]
        .as_str()
        .context("Invalid certificate generation")?;
    ensure!(
        name.len() == 64 && name.bytes().all(|b| b.is_ascii_hexdigit()),
        "Unsafe certificate generation"
    );
    let folder = root.join(name).canonicalize()?;
    ensure!(
        folder.parent() == Some(root.canonicalize()?.as_path()),
        "Certificate path escapes package"
    );
    ensure!(
        apk::digest(&folder.join("cacerts"))? == v["jks_sha256"].as_str().unwrap_or("")
            && apk::digest(&folder.join("ca-bundle.pem"))?
                == v["pem_sha256"].as_str().unwrap_or(""),
        "Certificate store integrity mismatch"
    );
    ensure!(
        apk::digest(&folder.join("certificates.json"))? == name,
        "Certificate metadata integrity mismatch"
    );
    Ok(Some(folder))
}
pub fn list(manager: &Manager, package: &str) -> Result<Value> {
    manager.get(package)?;
    let content = match current(manager, package)? {
        Some(path) => serde_json::from_slice::<Value>(&fs::read(path.join("certificates.json"))?)?,
        None => json!({"certificates":[],"scope":"system roots only"}),
    };
    Ok(json!({"ok":true,"package":package,"trust":content}))
}
pub fn update(manager: &Manager, package: &str, action: &str, value: &str) -> Result<Value> {
    manager.get(package)?;
    let _guard = manager.operation_lock(package)?;
    let existing = current(manager, package)?;
    let root = manager.root.join("certificates").join(package);
    fs::create_dir_all(&root)?;
    ensure!(
        !root.symlink_metadata()?.file_type().is_symlink(),
        "Unsafe certificate directory"
    );
    let stage = tempfile::tempdir_in(&root)?;
    let mut cmd = runtime::sandbox(false)?;
    cmd.arg("--ro-bind")
        .arg(runtime::share().canonicalize()?)
        .arg("/runtime");
    cmd.arg("--bind").arg(stage.path()).arg("/output");
    if let Some(path) = existing {
        cmd.arg("--ro-bind").arg(path).arg("/existing");
    } else {
        cmd.args(["--dir", "/existing"]);
    }
    if action == "add" {
        let input = PathBuf::from(value).canonicalize()?;
        ensure!(
            input.is_file() && input.metadata()?.len() <= 65536,
            "Public certificate size limit"
        );
        cmd.arg("--ro-bind").arg(input).arg("/input.pem");
    }
    cmd.args([
        "--",
        "/usr/bin/timeout",
        "--kill-after=2",
        "60",
        "/usr/bin/python3",
        "/runtime/certificates.py",
        action,
        if action == "add" { "" } else { value },
    ]);
    let output = cmd.output()?;
    ensure!(
        output.status.success(),
        "Certificate validation failed: {}",
        String::from_utf8_lossy(&output.stderr)
            .chars()
            .take(1500)
            .collect::<String>()
    );
    let generation = apk::digest(&stage.path().join("certificates.json"))?;
    let pointer = json!({"generation":generation,"jks_sha256":apk::digest(&stage.path().join("cacerts"))?,"pem_sha256":apk::digest(&stage.path().join("ca-bundle.pem"))?});
    let destination = root.join(&generation);
    if destination.exists() {
        // Reusing an identical trust set must retain its actual stored hashes.
        manager::atomic_json(
            &root.join("current.json"),
            &json!({"generation":generation,"jks_sha256":apk::digest(&destination.join("cacerts"))?,"pem_sha256":apk::digest(&destination.join("ca-bundle.pem"))?}),
        )?;
    } else {
        fs::rename(stage.path(), &destination)?;
        manager::atomic_json(&root.join("current.json"), &pointer)?;
    }
    let result: Value = serde_json::from_slice(&output.stdout)?;
    Ok(json!({"ok":true,"package":package,"result":result,"trust":list(manager,package)?["trust"]}))
}
