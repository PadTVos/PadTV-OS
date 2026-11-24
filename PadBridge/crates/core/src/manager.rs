use crate::apk::{self, App};
use anyhow::{ensure, Context, Result};
use fs2::FileExt;
use serde_json::{json, Value};
use std::{
    fs::{self, File, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};

pub struct Manager {
    pub root: PathBuf,
    _lock: File,
}
impl Manager {
    pub fn new(root: PathBuf) -> Result<Self> {
        fs::create_dir_all(&root)?;
        ensure!(
            !root.symlink_metadata()?.file_type().is_symlink(),
            "Data root must not be a symlink"
        );
        let lock = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(root.join(".lock"))?;
        lock.try_lock_exclusive()
            .context("Another PadBridge operation is running")?;
        for folder in ["packages", "data", "permissions", "locks", "logs"] {
            fs::create_dir_all(root.join(folder))?;
        }
        Ok(Self {
            root: root.canonicalize()?,
            _lock: lock,
        })
    }
    pub fn unlock(&self) -> Result<()> {
        FileExt::unlock(&self._lock)?;
        Ok(())
    }
    pub fn app_dir(&self, package: &str) -> Result<PathBuf> {
        ensure!(apk::valid_package(package), "Invalid package identifier");
        let path = self.root.join("packages").join(package);
        if path.exists() {
            ensure!(
                !path.symlink_metadata()?.file_type().is_symlink(),
                "Unsafe package directory"
            );
        }
        Ok(path)
    }
    pub fn get(&self, package: &str) -> Result<App> {
        let app: App =
            serde_json::from_slice(&fs::read(self.app_dir(package)?.join("current.json"))?)?;
        ensure!(
            app.package == package
                && app.sha256.len() == 64
                && app.sha256.bytes().all(|b| b.is_ascii_hexdigit())
                && app.storage_id().len() == 64
                && app.storage_id().bytes().all(|b| b.is_ascii_hexdigit()),
            "Invalid installed metadata"
        );
        Ok(app)
    }
    pub fn list(&self) -> Result<Vec<App>> {
        let mut apps = vec![];
        for entry in fs::read_dir(self.root.join("packages"))? {
            let name = entry?.file_name().to_string_lossy().into_owned();
            if let Ok(app) = self.get(&name) {
                apps.push(app);
            }
        }
        apps.sort_by(|a, b| a.package.cmp(&b.package));
        Ok(apps)
    }
    pub fn operation_lock(&self, package: &str) -> Result<File> {
        ensure!(apk::valid_package(package), "Invalid package identifier");
        let f = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(self.root.join("locks").join(package))?;
        f.try_lock_exclusive().context(
            "Application is running; close it before changing its installation or permissions",
        )?;
        Ok(f)
    }
    pub fn install(&self, source: &Path) -> Result<Value> {
        self.install_set(&[source.to_path_buf()])
    }
    pub fn install_set(&self, sources: &[PathBuf]) -> Result<Value> {
        let bundle = crate::bundles::Bundle::load(sources, &self.root)?;
        let source = &bundle.paths[0];
        let mut copy = tempfile::NamedTempFile::new_in(&self.root)?;
        ensure!(
            source.metadata()?.is_file() && source.metadata()?.len() <= apk::MAX_APK,
            "Invalid APK size"
        );
        std::io::copy(&mut File::open(source)?.take(apk::MAX_APK + 1), &mut copy)?;
        let app = bundle.app;
        let _guard = self.operation_lock(&app.package)?;
        if self.app_dir(&app.package)?.join("current.json").exists() {
            let old = self
                .get(&app.package)
                .context("Installed metadata is damaged; refusing to replace signer identity")?;
            ensure!(
                old.signers == app.signers,
                "APK signer differs from installed package; key rotation is not yet supported"
            );
            ensure!(
                app.version_code >= old.version_code,
                "APK downgrade is not allowed"
            );
            ensure!(
                app.version_code != old.version_code || app.storage_id() == old.storage_id(),
                "Different APK requires a higher versionCode"
            );
        }
        let folder = self.app_dir(&app.package)?;
        fs::create_dir_all(&folder)?;
        let version = folder.join(app.storage_id());
        if !version.exists() {
            let stage = tempfile::tempdir_in(&folder)?;
            fs::copy(copy.path(), stage.path().join("original.apk"))?;
            fs::create_dir_all(stage.path().join("splits"))?;
            for (split, path) in app.splits.iter().zip(bundle.paths.iter().skip(1)) {
                fs::copy(
                    path,
                    stage
                        .path()
                        .join("splits")
                        .join(format!("{}.apk", split.name)),
                )?;
            }
            let mut zip = apk::archive(copy.path())?;
            if let Some(ref name) = app.icon {
                let icon = apk::read_entry(&mut zip, name)?;
                ensure!(icon.len() <= 4 * 1024 * 1024, "Icon exceeds limit");
                fs::write(stage.path().join("icon"), icon)?;
            }
            fs::rename(stage.path(), &version)?;
        }
        // Keep data and explicit permission choices across updates. Default network is denied.
        fs::create_dir_all(self.root.join("data").join(&app.package))?;
        atomic_json(&folder.join("current.json"), &serde_json::to_value(&app)?)?;
        Ok(json!({"ok":true,"installed":true,"app":app,"experimental":true}))
    }
    pub fn remove(&self, package: &str, delete_data: bool) -> Result<Value> {
        let _guard = self.operation_lock(package)?;
        let folder = self.app_dir(package)?;
        ensure!(
            folder.join("current.json").exists(),
            "Application is not installed"
        );
        // Rename removes it atomically from the inventory; locked package cannot be running.
        let tomb = tempfile::tempdir_in(self.root.join("packages"))?;
        fs::rename(&folder, tomb.path().join("removed"))?;
        if delete_data {
            safe_remove(&self.root.join("data").join(package))?;
        }
        let grants = self
            .root
            .join("permissions")
            .join(format!("{package}.json"));
        if grants.exists() {
            fs::remove_file(grants)?;
        }
        Ok(json!({"ok":true,"removed":true,"data_deleted":delete_data}))
    }
    pub fn grants(&self, package: &str) -> Result<Vec<String>> {
        ensure!(apk::valid_package(package), "Invalid package identifier");
        let p = self
            .root
            .join("permissions")
            .join(format!("{package}.json"));
        if !p.exists() {
            return Ok(vec![]);
        }
        Ok(serde_json::from_slice(&fs::read(p)?)?)
    }
    pub fn permissions(&self, package: &str, grants: Option<Vec<String>>) -> Result<Value> {
        let app = self.get(package)?;
        if let Some(values) = grants {
            let _guard = self.operation_lock(package)?;
            ensure!(
                values
                    .iter()
                    .all(|p| p == "android.permission.INTERNET" && app.permissions.contains(p)),
                "Only declared INTERNET access can currently be granted"
            );
            atomic_json(
                &self
                    .root
                    .join("permissions")
                    .join(format!("{package}.json")),
                &json!(values),
            )?;
        }
        Ok(
            json!({"ok":true,"requested":app.permissions,"granted":self.grants(package)?,"supported":["android.permission.INTERNET"]}),
        )
    }
}
use std::io::Read;
fn safe_remove(path: &Path) -> Result<()> {
    if path.is_symlink() {
        fs::remove_file(path)?;
    } else if path.exists() {
        fs::remove_dir_all(path)?;
    }
    Ok(())
}
pub fn atomic_json(path: &Path, value: &Value) -> Result<()> {
    let mut temp = tempfile::NamedTempFile::new_in(path.parent().context("No parent")?)?;
    temp.write_all(serde_json::to_string_pretty(value)?.as_bytes())?;
    temp.as_file().sync_all()?;
    temp.persist(path)?;
    Ok(())
}
