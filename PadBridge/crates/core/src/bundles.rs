//! Verified split sets, retained byte-for-byte. No ZIP entry is extracted by path.
use crate::apk::{self, App, Split};
use anyhow::{ensure, Context, Result};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeSet,
    fs,
    io::Read,
    path::{Path, PathBuf},
};

pub struct Bundle {
    pub app: App,
    pub paths: Vec<PathBuf>,
    _stage: tempfile::TempDir,
}
impl Bundle {
    pub fn load(inputs: &[PathBuf], root: &Path) -> Result<Self> {
        ensure!(
            !inputs.is_empty() && inputs.len() <= 64,
            "Supply between 1 and 64 APKs"
        );
        let stage = tempfile::tempdir_in(root)?;
        let mut paths = vec![];
        let mut total = 0u64;
        for input in inputs {
            ensure!(
                input.metadata()?.is_file() && input.metadata()?.len() <= apk::MAX_APK,
                "Invalid APK/container size"
            );
            if matches!(
                input.extension().and_then(|s| s.to_str()),
                Some("apks" | "apkm")
            ) {
                let mut zip = zip::ZipArchive::new(fs::File::open(input)?)?;
                ensure!(zip.len() <= 256, "Too many container entries");
                for i in 0..zip.len() {
                    let entry = zip.by_index(i)?;
                    ensure!(
                        entry.enclosed_name().is_some()
                            && !entry.name().contains('\\')
                            && !entry.name().contains(':'),
                        "Unsafe split container path"
                    );
                    if !entry.name().ends_with(".apk") {
                        continue;
                    }
                    ensure!(entry.size() <= apk::MAX_APK, "Oversized split APK");
                    let path = stage.path().join(format!("{}.apk", paths.len()));
                    let n = std::io::copy(
                        &mut entry.take(apk::MAX_APK + 1),
                        &mut fs::File::create(&path)?,
                    )?;
                    total += n;
                    paths.push(path);
                    ensure!(
                        total <= 1024 * 1024 * 1024 && paths.len() <= 64,
                        "Split set exceeds limits"
                    );
                }
            } else {
                let path = stage.path().join(format!("{}.apk", paths.len()));
                total += std::io::copy(
                    &mut fs::File::open(input)?.take(apk::MAX_APK + 1),
                    &mut fs::File::create(&path)?,
                )?;
                paths.push(path);
                ensure!(total <= 1024 * 1024 * 1024, "Split set exceeds limits");
            }
        }
        let mut items = paths
            .into_iter()
            .map(|p| Ok((apk::inspect(&p)?, p)))
            .collect::<Result<Vec<_>>>()?;
        ensure!(items.iter().filter(|(a,_)|a.split.is_none()).count()==1,"A split set must contain exactly one base APK; device selection from bundletool archives is not automatic");
        items.sort_by(|a, b| a.0.split.cmp(&b.0.split));
        let (mut app, base) = items.remove(0);
        let mut paths = vec![base];
        let mut names = BTreeSet::new();
        for (meta, path) in items {
            ensure!(
                meta.package == app.package
                    && meta.version_code == app.version_code
                    && meta.signers == app.signers,
                "Split package, version or verified signer differs from base"
            );
            let name = meta.split.context("Missing split name")?;
            ensure!(names.insert(name.clone()), "Duplicate split identifier");
            app.splits.push(Split {
                name,
                sha256: meta.sha256,
            });
            for permission in meta.permissions {
                if !app.permissions.contains(&permission) {
                    app.permissions.push(permission);
                }
            }
            for abi in meta.abis {
                if !app.abis.contains(&abi) {
                    app.abis.push(abi);
                }
            }
            paths.push(path);
        }
        if !app.splits.is_empty() {
            let mut hash = Sha256::new();
            hash.update(app.sha256.as_bytes());
            for split in &app.splits {
                hash.update(split.name.as_bytes());
                hash.update([0]);
                hash.update(split.sha256.as_bytes());
            }
            app.installation_id = format!("{:x}", hash.finalize());
        }
        Ok(Self {
            app,
            paths,
            _stage: stage,
        })
    }
}
