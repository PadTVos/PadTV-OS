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

const ABI_LIBRARIES: &[&str] = &["libc.so", "libm.so", "libdl.so", "liblog.so"];
// No Bionic structure-bearing calls, pthread ABI, Android TLS or dynamic linking.
const ABI_SYMBOLS: &[&str] = &[
    "malloc",
    "calloc",
    "realloc",
    "free",
    "memcpy",
    "memmove",
    "memset",
    "memcmp",
    "memchr",
    "strlen",
    "strcmp",
    "strncmp",
    "strcpy",
    "strncpy",
    "strchr",
    "strrchr",
    "strstr",
    "strdup",
    "atoi",
    "atol",
    "strtol",
    "strtoul",
    "strtoll",
    "strtoull",
    "strtod",
    "abort",
    "getpid",
    "sin",
    "cos",
    "tan",
    "sqrt",
    "pow",
    "exp",
    "log",
    "floor",
    "ceil",
    "fabs",
    "fmod",
    "sinf",
    "cosf",
    "sqrtf",
    "powf",
    "floorf",
    "ceilf",
    "fabsf",
    "fmodf",
    "__cxa_finalize",
    "__cxa_atexit",
    "__stack_chk_fail",
    "__errno",
    "__assert2",
    "__system_property_get",
    "__android_log_write",
    "__android_log_print",
];

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
            let unsupported_symbols: Vec<_> = undefined
                .iter()
                .filter(|s| !ABI_SYMBOLS.contains(s))
                .collect();
            let unsupported_libraries: Vec<_> = elf
                .libraries
                .iter()
                .filter(|s| !ABI_LIBRARIES.contains(s))
                .collect();
            let versioned = elf
                .verneed
                .as_ref()
                .map(|v| v.iter().next().is_some())
                .unwrap_or(false);
            let supported = elf.is_64
                && elf.little_endian
                && elf.header.e_machine == 62
                && elf.header.e_type == 3
                && elf.interpreter.is_none()
                && !tls
                && unsupported_libraries.is_empty()
                && unsupported_symbols.is_empty()
                && !versioned;
            json!({"path":name,"elf_machine":elf.header.e_machine,"is_64_bit":elf.is_64,
                "architecture":match elf.header.e_machine {62=>"x86_64",3=>"x86",183=>"aarch64",40=>"arm",_=>"unknown"},
                "needed":elf.libraries,"undefined_symbols":undefined,"tls":tls,
                "supported":supported,"loader":if elf.libraries.is_empty()&&undefined.is_empty(){"sandboxed-host-loader-freestanding-only"}else{"sandboxed-host-loader-limited-unversioned-abi"},
                "versioned_imports":versioned,"unsupported_symbols":unsupported_symbols,
                "unresolved_android_abi_dependencies":unsupported_libraries,
                "error":if supported {Value::Null} else {json!("Requires little-endian x86-64 ET_DYN without TLS/versioned imports and only approved scalar/memory ABI symbols. Full Bionic, Android linker and ARM translation are unavailable")}})
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
                // Optional native libraries must not prevent original Java code
                // from starting. Unsupported bytes are never loaded: the JVM
                // raises UnsatisfiedLinkError if the app actually requests them.
                if report["supported"] != true {
                    continue;
                }
                ensure!(
                    selected.insert(parts[2].to_owned(), data).is_none(),
                    "Duplicate native library in splits"
                );
            }
        }
    }
    // Full ABI diagnostics remain in inspect/analyze; no host library substitution.
    Ok(selected)
}

pub fn stage(paths: &[PathBuf], parent: &Path) -> Result<tempfile::TempDir> {
    let stage = tempfile::tempdir_in(parent)?;
    for (name, bytes) in selected(paths)? {
        ensure!(
            !ABI_LIBRARIES.contains(&name.as_str()),
            "APK cannot replace the native ABI adapter"
        );
        fs::write(stage.path().join(name), bytes)?;
    }
    let adapter = crate::runtime::share().join("libpadbridge_bionic_abi.so");
    for name in ABI_LIBRARIES {
        fs::copy(&adapter, stage.path().join(name))?;
    }
    Ok(stage)
}
