mod analyzer;
mod apk;
mod backends;
mod bundles;
mod dex;
mod manager;
mod media;
mod native_elf;
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
        "analyze" => {
            let split = args
                .iter()
                .position(|s| s == "--html")
                .unwrap_or(args.len());
            let html = if split < args.len() {
                Some(arg(split + 1)?.as_str())
            } else {
                None
            };
            analyzer::analyze(
                &manager,
                &args[1..split].iter().map(PathBuf::from).collect::<Vec<_>>(),
                html,
            )
        }
        "inspect" | "diagnose" => {
            let path = PathBuf::from(arg(1)?);
            let meta = apk::inspect(&path)?;
            Ok(json!({"ok":true,"app":meta,"diagnostics":dex::diagnose(&path)?}))
        }
        "install" => manager.install(&PathBuf::from(arg(1)?)),
        "install-set" => {
            manager.install_set(&args[1..].iter().map(PathBuf::from).collect::<Vec<_>>())
        }
        "inspect-set" => {
            let set = bundles::Bundle::load(
                &args[1..].iter().map(PathBuf::from).collect::<Vec<_>>(),
                &manager.root,
            )?;
            Ok(json!({"ok":true,"app":set.app,"diagnostics":dex::diagnose_set(&set.paths)?}))
        }
        "backends" => Ok(json!({"ok":true,"backends":backends::list()})),
        "media-probe" | "media-decode" => {
            media::probe(&PathBuf::from(arg(1)?), action == "media-decode")
        }
        "list" => Ok(json!({"ok":true,"apps":manager.list()?})),
        "diagnose-installed" => {
            let app = manager.get(arg(1)?)?;
            let folder = manager.app_dir(&app.package)?.join(app.storage_id());
            let mut paths = vec![folder.join("original.apk")];
            for split in &app.splits {
                anyhow::ensure!(
                    !split.name.contains('/')
                        && !split.name.contains('\\')
                        && !split.name.contains(".."),
                    "Unsafe split name"
                );
                paths.push(folder.join("splits").join(format!("{}.apk", split.name)));
            }
            let log = std::fs::read_to_string(
                manager
                    .root
                    .join("logs")
                    .join(format!("{}.log", app.package)),
            )
            .unwrap_or_default();
            let tail = log
                .chars()
                .rev()
                .take(4000)
                .collect::<String>()
                .chars()
                .rev()
                .collect::<String>();
            Ok(
                json!({"ok":true,"app":app,"diagnostics":dex::diagnose_set(&paths)?,"last_error":tail}),
            )
        }
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
            args.iter()
                .position(|s| s == "--backend")
                .map(|i| arg(i + 1))
                .transpose()?
                .map(String::as_str)
                .unwrap_or("enjarify-openjdk"),
        ),
        "capabilities" => Ok(json!({"ok":true,"version":env!("CARGO_PKG_VERSION"),
            "stage":"experimental", "backend":"enjarify-openjdk", "requires_android_os":false,
            "backends":backends::list(), "sandbox":"bubblewrap-required", "secure_media":secure_media::capabilities(),
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
