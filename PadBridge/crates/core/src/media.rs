//! FFmpeg decoding of unprotected local media, isolated from network and home.
use crate::{apk, runtime};
use anyhow::{ensure, Context, Result};
use serde_json::{json, Value};
use std::{fs, path::Path};
pub fn probe(path: &Path, decode: bool) -> Result<Value> {
    let input = path.canonicalize()?;
    ensure!(
        input.is_file() && input.metadata()?.len() <= 4 * 1024 * 1024 * 1024,
        "Local media must be a file no larger than 4 GiB"
    );
    let mut command = runtime::sandbox(false)?;
    command.arg("--ro-bind").arg(&input).arg("/input.media");
    command.args([
        "--",
        "/usr/bin/timeout",
        "--kill-after=2",
        "30",
        "/usr/bin/ffprobe",
        "-v",
        "error",
        "-protocol_whitelist",
        "file,pipe",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        "/input.media",
    ]);
    let out = command.output().context("FFprobe is unavailable")?;
    ensure!(
        out.status.success(),
        "Media probe failed: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    ensure!(
        out.stdout.len() < 8 * 1024 * 1024,
        "Media metadata exceeds limit"
    );
    let info: Value = serde_json::from_slice(&out.stdout)?;
    if !decode {
        return Ok(json!({"ok":true,"engine":"ffmpeg","protected_playback":false,"media":info}));
    }
    let stage = tempfile::tempdir()?;
    let mut command = runtime::sandbox(false)?;
    command.arg("--ro-bind").arg(&input).arg("/input.media");
    command.arg("--bind").arg(stage.path()).arg("/output");
    command.args([
        "--",
        "/usr/bin/timeout",
        "--kill-after=2",
        "30",
        "/usr/bin/ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        "/input.media",
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
        "-vf",
        "scale=640:360:force_original_aspect_ratio=decrease",
        "-threads",
        "2",
        "-fs",
        "4194304",
        "/output/frame.png",
    ]);
    let out = command.output().context("FFmpeg is unavailable")?;
    ensure!(
        out.status.success(),
        "Media decode failed: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let frame = stage.path().join("frame.png");
    let bytes = fs::metadata(&frame)?.len();
    ensure!(
        bytes > 8 && bytes <= 4 * 1024 * 1024,
        "Decoded frame size invalid"
    );
    Ok(
        json!({"ok":true,"engine":"ffmpeg-software","decoded_frames":1,"frame_sha256":apk::digest(&frame)?,"frame_bytes":bytes,"media":info,
        "hardware_acceleration_verified":false,"protected_playback":false}),
    )
}
