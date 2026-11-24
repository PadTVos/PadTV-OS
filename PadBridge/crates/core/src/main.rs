mod apk;
mod dex;
mod manager;
mod runtime;
mod secure_media;

use anyhow::{bail, Context, Result};
use serde_json::{json, Value};
use std::{env, path::PathBuf};

fn dispatch() -> Result<Value> {
    let args: Vec<String> = env::args().skip(1).collect();
    let action = args.first().map(String::as_str).unwrap_or("capabilities");
    let arg = |i: usize| args.get(i).context("Missing argument");
    let root = env::var_os("PADBRIDGE_DATA_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            env::var_os("XDG_DATA_HOME")
                .map(PathBuf::from)
                .unwrap_or_else(|| {
                    PathBuf::from(env::var_os("HOME").unwrap_or_default()).join(".local/share")
                })
                .join("padbridge")
        });
    let manager = manager::Manager::new(root)?;
    match action {
        "inspect" | "diagnose" => {
            let path = PathBuf::from(arg(1)?);
            let meta = apk::inspect(&path)?;
            Ok(json!({"ok":true,"app":meta,"diagnostics":dex::diagnose(&path)?}))
        }
        "install" => manager.install(&PathBuf::from(arg(1)?)),
        "list" => Ok(json!({"ok":true,"apps":manager.list()?})),
        "remove" => manager.remove(arg(1)?, args.iter().any(|a| a == "--delete-data")),
        "permissions" => {
            let package = arg(1)?;
            if let Some(value) = args.get(2) {
                let grants: Vec<String> = serde_json::from_str(value)?;
                manager.permissions(package, Some(grants))
            } else {
                manager.permissions(package, None)
            }
        }
        "run" => runtime::run(
            &manager,
            arg(1)?,
            args.iter().any(|s| s == "--headless"),
            args.iter().any(|s| s == "--restart-once"),
        ),
        "capabilities" => Ok(json!({"ok":true,"version":env!("CARGO_PKG_VERSION"),
            "stage":"experimental", "backend":"enjarify-openjdk", "requires_android_os":false,
            "sandbox":"bubblewrap-required", "secure_media":secure_media::capabilities(),
            "apis":serde_json::from_str::<Value>(include_str!("../../../api/compatibility.json"))?})),
        _ => bail!("Unknown command: {action}"),
    }
}

fn main() {
    match dispatch() {
        Ok(value) => {
            println!("{value}");
            if value.get("ok") == Some(&Value::Bool(false)) {
                std::process::exit(1);
            }
        }
        Err(error) => {
            println!("{}", json!({"ok":false,"error":format!("{error:#}")}));
            std::process::exit(1);
        }
    }
}
