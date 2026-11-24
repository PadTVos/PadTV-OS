use serde_json::{json, Value};
/// Evidence rather than a certification claim. A SecureBoot EFI variable alone
/// cannot attest the entire userspace/video path.
pub fn capabilities() -> Value {
    let secure_boot = std::fs::read_dir("/sys/firmware/efi/efivars")
        .ok()
        .and_then(|entries| {
            entries
                .flatten()
                .find(|e| e.file_name().to_string_lossy().starts_with("SecureBoot-"))
                .and_then(|e| std::fs::read(e.path()).ok())
                .and_then(|b| b.get(4).copied())
                .map(|v| v == 1)
        });
    json!({"secure_boot_firmware":secure_boot,"system_integrity_attested":false,
        "signed_update_enforcement":false,"hdcp":"unprobed","tee":"unprobed",
        "secure_video_pipeline":false,"licensed_widevine":false,"widevine_security_level":null,
        "netflix_certified":false,"protected_4k_hdr":false})
}
