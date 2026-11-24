#!/bin/bash
set -euo pipefail
padtv_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for padtv_tool in mkfs.ext4 qemu-img truncate; do
    command -v "$padtv_tool" >/dev/null || { echo "Chybí $padtv_tool." >&2; exit 1; }
done
mkdir -p "$padtv_root/build" "$padtv_root/dist"
padtv_work=$(mktemp -d "$padtv_root/build/persistence.XXXXXXXX")
trap 'rm -rf -- "$padtv_work"' EXIT
mkdir "$padtv_work/content"
cat > "$padtv_work/content/persistence.conf" <<'EOF'
/home union
/var/lib/padtv union
/var/lib/waydroid union
/var/lib/bluetooth union
/var/lib/NetworkManager union
/etc/NetworkManager/system-connections union
EOF
truncate -s 64G "$padtv_work/disk.raw"
# Format only a newly created regular file, never a device or an existing VM disk.
mkfs.ext4 -q -F -L persistence -m 0 -d "$padtv_work/content" "$padtv_work/disk.raw"
qemu-img convert -c -f raw -O qcow2 "$padtv_work/disk.raw" "$padtv_work/template.qcow2"
mv -- "$padtv_work/template.qcow2" "$padtv_root/dist/padtv-persistence-v2-64G.qcow2"
echo "Hotovo: $padtv_root/dist/padtv-persistence-v2-64G.qcow2"
