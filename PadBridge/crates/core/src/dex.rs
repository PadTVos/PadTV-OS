//! Bounded DEX metadata reader. Bytecode execution is delegated to the strict
//! Enjarify/JVM backend, not reimplemented here.
use crate::apk;
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{collections::BTreeSet, path::Path};

fn u32_at(data: &[u8], at: usize) -> Result<usize> {
    Ok(u32::from_le_bytes(data.get(at..at + 4).context("Truncated DEX")?.try_into()?) as usize)
}
pub fn types(data: &[u8]) -> Result<Vec<String>> {
    ensure!(
        data.len() >= 112 && &data[..4] == b"dex\n" && data[7] == 0,
        "Invalid DEX header"
    );
    ensure!(
        &data[4..7] == b"035",
        "DEX version unsupported by experimental backend (requires 035)"
    );
    ensure!(
        u32_at(data, 32)? == data.len() && u32_at(data, 40)? == 0x12345678,
        "Invalid DEX size or endian marker"
    );
    let count = u32_at(data, 56)?;
    let offset = u32_at(data, 60)?;
    ensure!(
        count <= 1_000_000 && offset + count * 4 <= data.len(),
        "Invalid DEX string table"
    );
    let mut strings = vec![];
    for i in 0..count {
        let mut at = u32_at(data, offset + i * 4)?;
        let mut ended = false;
        for _ in 0..5 {
            let byte = *data.get(at).context("Truncated DEX string")?;
            at += 1;
            if byte & 128 == 0 {
                ended = true;
                break;
            }
        }
        ensure!(ended, "Invalid DEX string length");
        let rest = data.get(at..).context("Invalid DEX string offset")?;
        let end = rest
            .iter()
            .take(1024 * 1024)
            .position(|b| *b == 0)
            .context("Unterminated DEX string")?;
        strings.push(String::from_utf8_lossy(&rest[..end]).into_owned());
    }
    let n = u32_at(data, 64)?;
    let off = u32_at(data, 68)?;
    ensure!(
        n <= 65536 && off + n * 4 <= data.len(),
        "Invalid DEX type table"
    );
    (0..n)
        .map(|i| {
            strings
                .get(u32_at(data, off + i * 4)?)
                .cloned()
                .context("Invalid type string index")
        })
        .collect()
}
pub fn diagnose(path: &Path) -> Result<Value> {
    let mut zip = apk::archive(path)?;
    let names: Vec<String> = zip.file_names().map(str::to_owned).collect();
    let supported: Value = serde_json::from_str(include_str!("../../../api/compatibility.json"))?;
    let classes: BTreeSet<&str> = supported["classes"]
        .as_array()
        .context("API registry")?
        .iter()
        .filter_map(Value::as_str)
        .collect();
    let mut missing = BTreeSet::new();
    let mut errors = vec![];
    let mut dex_count = 0;
    for name in names
        .iter()
        .filter(|n| n.ends_with(".dex") && !n.contains('/'))
    {
        dex_count += 1;
        match types(&apk::read_entry(&mut zip, name)?) {
            Ok(values) => {
                for t in values {
                    let name = t
                        .trim_start_matches('[')
                        .trim_start_matches('L')
                        .trim_end_matches(';')
                        .replace('/', ".");
                    if (name.starts_with("android.")
                        || name.starts_with("androidx.")
                        || name.starts_with("com.google.android.gms."))
                        && !classes.contains(name.as_str())
                    {
                        missing.insert(name);
                    }
                }
            }
            Err(error) => errors.push(format!("{name}: {error}")),
        }
    }
    let native: Vec<&String> = names
        .iter()
        .filter(|n| n.starts_with("lib/") && n.ends_with(".so"))
        .collect();
    let mut libraries = vec![];
    for name in &native {
        let bytes = apk::read_entry(&mut zip, name)?;
        let detail = match goblin::elf::Elf::parse(&bytes) {
            Ok(elf) => json!({"path":name,"elf_machine":elf.header.e_machine,"is_64_bit":elf.is_64,
                "needed":elf.libraries,"unresolved_android_abi_dependencies":elf.libraries,
                "error":"Android/Bionic native loader is not implemented; host glibc libraries cannot satisfy this ABI"}),
            Err(error) => json!({"path":name,"error":format!("Invalid ELF: {error}")}),
        };
        libraries.push(detail);
    }
    Ok(
        json!({"backend":"enjarify-openjdk","dex_files":dex_count,"unsupported_classes":missing,
        "dex_errors":errors,"native_libraries":native,"native_details":libraries,"native_abi_supported":native.is_empty(),
        "drm":"No licensed MediaDrm provider; Widevine and protected video unavailable",
        "assessment":"Static class references only; method signatures, reflection, resources and behavior require execution tests",
        "eligible_for_trial":missing.is_empty() && errors.is_empty() && native.is_empty()}),
    )
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_truncated() {
        for n in 0..112 {
            assert!(types(&vec![0; n]).is_err());
        }
    }
    #[test]
    fn rejects_bad_tables() {
        let mut d = vec![0u8; 112];
        d[..8].copy_from_slice(b"dex\n035\0");
        d[32..36].copy_from_slice(&112u32.to_le_bytes());
        d[40..44].copy_from_slice(&0x12345678u32.to_le_bytes());
        d[56..60].copy_from_slice(&u32::MAX.to_le_bytes());
        assert!(types(&d).is_err());
    }
}
