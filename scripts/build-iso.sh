#!/bin/bash
set -euo pipefail
padtv_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
padtv_version=$(PYTHONPATH="$padtv_root" python3 -c 'from padtv import __version__; print(__version__)')
if [ "$(id -u)" -ne 0 ]; then
    echo "Sestavení vyžaduje root: sudo bash scripts/build-iso.sh" >&2
    exit 1
fi
# shellcheck source=/dev/null
. /etc/os-release
if [ "${ID:-}" != debian ] || [ "${VERSION_ID:-}" != 13 ]; then
    echo "Použijte Debian 13 amd64 (samostatný build stroj, VM nebo kontejner s podporou mount)." >&2
    exit 1
fi
if [ "$(dpkg --print-architecture)" != amd64 ]; then
    echo "Tento první profil podporuje pouze amd64." >&2
    exit 1
fi
for tool in lb debootstrap xorriso mksquashfs; do
    command -v "$tool" >/dev/null || { echo "Chybí $tool; viz README.md." >&2; exit 1; }
done
mkdir -p "$padtv_root/build" "$padtv_root/dist"
padtv_work=$(mktemp -d "$padtv_root/build/live.XXXXXXXX")
cp -a "$padtv_root/live/." "$padtv_work/"
bash "$padtv_root/scripts/build-deb.sh" "$padtv_work/config/packages.chroot"
bash "$padtv_root/scripts/build-exo-fix.sh" "$padtv_work/config/packages.chroot"
chmod +x "$padtv_work/auto/config" "$padtv_work/config/hooks/live/0100-padtv.hook.chroot"
chmod +x "$padtv_work/config/hooks/live/0200-padtv-boot.hook.binary"
cd "$padtv_work"
lb config
# pipefail preserves a build failure even though output is also recorded.
lb build 2>&1 | tee build.log
mapfile -t padtv_images < <(find "$padtv_work" -maxdepth 1 -name '*.iso' -type f)
if [ "${#padtv_images[@]}" -ne 1 ]; then
    echo "Očekáván právě jeden ISO obraz, nalezeno ${#padtv_images[@]}." >&2
    exit 1
fi
padtv_iso="padtv-${padtv_version}-amd64.iso"
cp -- "${padtv_images[0]}" "$padtv_root/dist/$padtv_iso"
cd "$padtv_root/dist"
sha256sum "$padtv_iso" > "$padtv_iso.sha256"
echo "Hotovo: $padtv_root/dist/$padtv_iso (balíčky $padtv_version)"
