# PadTV Secure Media Engine — planned integration

No licensed Widevine module, L1 implementation, HDCP enforcement, trusted video
path or Netflix certification ships in PadBridge. The `capabilities` command
reports absent components as false/unknown, and reads the firmware SecureBoot
variable only when accessible. That variable **does not attest userspace**.

The proposed trust path is firmware Secure Boot → signed bootloader/kernel/UKI
→ verified immutable system image → signed update metadata with rollback
protection → isolated media broker → licensed vendor CDM/OEMCrypto in a suitable
TEE → protected buffers and hardware decode/compositor → verified HDCP link.
The broker must refuse protected playback when any required capability is
missing. Unprotected FFmpeg playback, software DRM, TPM presence or a monitor's
HDCP capability cannot substitute for that whole chain.

Proposed interfaces (design only): `query_capabilities`, `open_licensed_session`,
`process_license_response`, `allocate_protected_surface`,
`validate_output_protection`, `close_session`. No key material crosses the
normal app API or appears in diagnostics. Plugin ABI/version, signature and
vendor ownership need validation before loading. Secure update signing keys
belong outside source control, with a documented key rotation/recovery process.
PadTV currently has a release-manifest signing tool, not an enforced signed OS
update/rollback chain.

[Google's Widevine onboarding](https://developers.google.com/widevine/access)
requires partner agreements and approved repository access. L1 device
integration needs the chipset vendor's OEMCrypto implementation.
[AOSP's DRM architecture](https://source.android.com/docs/core/media/drm)
describes protected keys, frames and outputs; a Java MediaDrm facade alone is
insufficient. [HDCP specifications/licensing](https://www.digital-cp.com/hdcp-specifications)
must be handled with licensed hardware and a compliant output path.

Netflix 4K HDR is a long-term product objective, not a promised software
feature. It needs an approved device/product, licensed playback stack,
compatible hardware and display link, supported codec/HDR path, service plan
and content. [Netflix device certification guidance](https://help.netflix.com/en/node/57688)
and [Ultra HD requirements](https://help.netflix.com/en/node/13444) must be checked
with the vendor during commercial integration. Do not copy device certificates,
spoof device identity, export keys or bypass license restrictions.
