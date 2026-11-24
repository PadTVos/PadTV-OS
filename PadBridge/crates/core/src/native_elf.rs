//! Deliberately limited first native path: dependency-free x86-64 ELF/JNI.
//! The Linux loader handles relocations inside the application sandbox. This is
//! NOT a Bionic implementation and must not accept DT_NEEDED or Android TLS.
use crate::apk;
use anyhow::{ensure, Result};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

pub fn inspect(name: &str, bytes: &[u8]) -> Value {
    match goblin::elf::Elf::parse(bytes) {
        Ok(elf) => {
            let undefined: Vec<_> = elf
                .dynsyms
                .iter()
                .filter(|s| s.st_shndx == 0 && s.st_name != 0)
                .filter_map(|s| elf.dynstrtab.get_at(s.st_name))
                .collect();
            let tls = elf
                .program_headers
                .iter()
                .any(|p| p.p_type == goblin::elf::program_header::PT_TLS);
            let supported = elf.is_64
                && elf.little_endian
                && elf.header.e_machine == 62
                && elf.header.e_type == 3
                && elf.interpreter.is_none()
                && !tls
                && elf.libraries.is_empty()
                && undefined.is_empty();
            json!({"path":name,"elf_machine":elf.header.e_machine,"is_64_bit":elf.is_64,
                "architecture":match elf.header.e_machine {62=>"x86_64",3=>"x86",183=>"aarch64",40=>"arm",_=>"unknown"},
                "needed":elf.libraries,"undefined_symbols":undefined,"tls":tls,
                "supported":supported,"loader":"sandboxed-host-loader-freestanding-only",
                "unresolved_android_abi_dependencies":elf.libraries,
                "error":if supported {Value::Null} else {json!("Requires dependency-free little-endian x86-64 ET_DYN without TLS or undefined symbols; Bionic, Android linker and ARM translation are unavailable")}})
        }
        Err(error) => {
            json!({"path":name,"supported":false,"error":format!("Invalid ELF: {error}")})
        }
    }
}

pub fn selected(paths: &[PathBuf]) -> Result<BTreeMap<String, Vec<u8>>> {
    let mut names = BTreeSet::new();
    let mut selected = BTreeMap::new();
    for path in paths {
        let mut zip = apk::archive(path)?;
        let entries: Vec<_> = zip.file_names().map(str::to_owned).collect();
        for name in entries
            .iter()
            .filter(|n| n.starts_with("lib/") && n.ends_with(".so"))
        {
            let parts: Vec<_> = name.split('/').collect();
            ensure!(parts.len() == 3, "Invalid native library path");
            names.insert(parts[2].to_owned());
            if parts[1] == "x86_64" {
                let data = apk::read_entry(&mut zip, name)?;
                let report = inspect(name, &data);
                ensure!(
                    report["supported"] == true,
                    "Unsupported native library: {report}"
                );
                ensure!(
                    selected.insert(parts[2].to_owned(), data).is_none(),
                    "Duplicate native library in splits"
                );
            }
        }
    }
    ensure!(names.len()==selected.len(), "Some native libraries have no x86-64 variant; ARM and 32-bit x86 translation are unavailable");
    Ok(selected)
}

pub fn stage(paths: &[PathBuf], parent: &Path) -> Result<tempfile::TempDir> {
    let stage = tempfile::tempdir_in(parent)?;
    for (name, bytes) in selected(paths)? {
        fs::write(stage.path().join(name), bytes)?;
    }
    Ok(stage)
}
