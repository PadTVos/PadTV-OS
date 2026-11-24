use anyhow::{bail, ensure, Context, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs::File, io::Read, path::Path};
use zip::ZipArchive;

pub const MAX_APK: u64 = 512 * 1024 * 1024;
pub const MAX_ENTRY: u64 = 64 * 1024 * 1024;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct App {
    pub package: String,
    pub title: String,
    pub version_code: u64,
    pub version_name: String,
    pub activity: String,
    pub sha256: String,
    pub signers: Vec<String>,
    pub permissions: Vec<String>,
    pub abis: Vec<String>,
    pub icon: Option<String>,
    pub television: bool,
}

pub fn valid_package(value: &str) -> bool {
    value.len() <= 240
        && value.contains('.')
        && value.split('.').all(|s| {
            !s.is_empty()
                && s.as_bytes()[0].is_ascii_alphabetic()
                && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_')
        })
}

pub fn digest(path: &Path) -> Result<String> {
    let mut source = File::open(path)?;
    let mut hash = Sha256::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = source.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hash.update(&buf[..n]);
    }
    Ok(format!("{:x}", hash.finalize()))
}

pub fn archive(path: &Path) -> Result<ZipArchive<File>> {
    let file = File::open(path)?;
    ensure!(
        file.metadata()?.len() <= MAX_APK,
        "APK exceeds 512 MiB limit"
    );
    let mut zip = ZipArchive::new(file)?;
    ensure!(zip.len() <= 20000, "Too many APK entries");
    let mut names = BTreeSet::new();
    let mut total = 0u64;
    for i in 0..zip.len() {
        let entry = zip.by_index(i)?;
        ensure!(
            entry.enclosed_name().is_some()
                && !entry.name().contains('\\')
                && !entry.name().starts_with('/')
                && !entry.name().contains(':'),
            "Unsafe APK path"
        );
        ensure!(names.insert(entry.name().to_owned()), "Duplicate APK entry");
        ensure!(
            entry.unix_mode().unwrap_or(0) & 0o170000 != 0o120000,
            "APK symlinks are not allowed"
        );
        ensure!(entry.size() <= MAX_ENTRY, "APK entry exceeds 64 MiB limit");
        total = total
            .checked_add(entry.size())
            .context("APK size overflow")?;
        ensure!(
            total <= 1024 * 1024 * 1024,
            "Expanded APK exceeds 1 GiB limit"
        );
    }
    ensure!(names.contains("AndroidManifest.xml") && names.contains("classes.dex"),
        "A standalone base APK with manifest and classes.dex is required; split APK sets are unsupported");
    Ok(zip)
}

pub fn command(program: &str, args: &[&str], seconds: u32) -> Result<String> {
    // Fixed executable, separate arguments, and a deadline. No shell evaluation.
    let mut sandbox = crate::runtime::sandbox(false)?;
    sandbox.args([
        "--ro-bind",
        args.last().context("Missing APK path")?,
        "/input.apk",
        "--",
        "/usr/bin/timeout",
        "--kill-after=3",
        &seconds.to_string(),
        program,
    ]);
    let output = sandbox
        .args(&args[..args.len() - 1])
        .arg("/input.apk")
        .output()
        .with_context(|| format!("Missing dependency or sandbox: {program}"))?;
    ensure!(
        output.status.success(),
        "{program}: {}",
        String::from_utf8_lossy(&output.stderr)
            .chars()
            .take(1500)
            .collect::<String>()
    );
    ensure!(
        output.stdout.len() < 8 * 1024 * 1024,
        "Tool output exceeds limit"
    );
    Ok(String::from_utf8(output.stdout)?)
}

fn field(text: &str, key: &str) -> Option<String> {
    let pattern = format!(r"(?:^|\s){}='([^']*)'", regex::escape(key));
    Regex::new(&pattern)
        .ok()?
        .captures(text)?
        .get(1)
        .map(|m| m.as_str().to_owned())
}

pub fn inspect(path: &Path) -> Result<App> {
    let zip = archive(path)?;
    let absolute = path.canonicalize()?;
    let path_arg = absolute.to_str().context("Non UTF-8 APK path")?;
    let signatures = command(
        "/usr/bin/apksigner",
        &["verify", "--print-certs", path_arg],
        45,
    )?;
    let mut signers: Vec<String> = signatures
        .lines()
        .filter_map(|line| {
            line.split_once(" certificate SHA-256 digest: ")
                .map(|(_, v)| v.trim().to_ascii_lowercase())
        })
        .collect();
    signers.sort();
    signers.dedup();
    ensure!(
        !signers.is_empty()
            && signers
                .iter()
                .all(|s| s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit())),
        "No verified APK signer"
    );
    let badging = command("/usr/bin/aapt", &["dump", "badging", path_arg], 30)?;
    let package_line = badging
        .lines()
        .find(|l| l.starts_with("package:"))
        .context("Missing package")?;
    ensure!(
        field(package_line, "split").is_none(),
        "Split APK installation is not supported"
    );
    let package = field(package_line, "name").context("Missing package name")?;
    ensure!(valid_package(&package), "Invalid package identifier");
    let activity_line = badging
        .lines()
        .find(|l| l.starts_with("launchable-activity:"))
        .or_else(|| {
            badging
                .lines()
                .find(|l| l.starts_with("leanback-launchable-activity:"))
        });
    let activity = activity_line
        .and_then(|l| field(l, "name"))
        .unwrap_or_default();
    let title = badging
        .lines()
        .find_map(|l| {
            l.strip_prefix("application-label:'")
                .and_then(|v| v.strip_suffix('\''))
        })
        .unwrap_or(&package)
        .chars()
        .filter(|c| !c.is_control())
        .take(120)
        .collect();
    let icon = activity_line
        .and_then(|l| field(l, "icon"))
        .filter(|s| !s.is_empty())
        .or_else(|| {
            badging
                .lines()
                .find(|l| l.starts_with("application:"))
                .and_then(|l| field(l, "icon"))
        })
        .filter(|s| s.ends_with(".png") || s.ends_with(".jpg") || s.ends_with(".webp"));
    let permissions = badging
        .lines()
        .filter(|l| l.starts_with("uses-permission:"))
        .filter_map(|l| field(l, "name"))
        .collect();
    let abis = zip
        .file_names()
        .filter_map(|n| n.strip_prefix("lib/")?.split('/').next().map(str::to_owned))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    Ok(App {
        package,
        title,
        activity,
        version_code: field(package_line, "versionCode")
            .context("Missing versionCode")?
            .parse()?,
        version_name: field(package_line, "versionName").unwrap_or_default(),
        sha256: digest(&absolute)?,
        signers,
        permissions,
        abis,
        icon,
        television: badging.contains("android.software.leanback")
            || badging.contains("leanback-launchable-activity"),
    })
}

pub fn read_entry(zip: &mut ZipArchive<File>, name: &str) -> Result<Vec<u8>> {
    let entry = zip.by_name(name)?;
    let expected = entry.size();
    ensure!(expected <= MAX_ENTRY, "Entry exceeds limit");
    let mut bytes = Vec::new();
    entry.take(MAX_ENTRY + 1).read_to_end(&mut bytes)?;
    if bytes.len() as u64 != expected {
        bail!("APK entry size mismatch");
    }
    Ok(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn package_paths() {
        for bad in ["../foo", "a/b.c", "a..b", "a.b-c", "com.1evil", "foo"] {
            assert!(!valid_package(bad));
        }
        assert!(valid_package("org.padtv.fixture"));
    }
    #[test]
    fn badging_attributes() {
        assert_eq!(
            field("package: name='a.b' versionCode='2'", "name").as_deref(),
            Some("a.b")
        );
        assert!(field("name='a.b'", "split").is_none());
    }
}
