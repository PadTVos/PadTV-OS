#!/bin/bash
# Rebuild Debian's library with the upstream fix for Home/End in empty folders.
set -euo pipefail
padtv_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
padtv_output=${1:-"$padtv_root/dist"}
mkdir -p -- "$padtv_output" "$padtv_root/build"
padtv_output=$(cd -- "$padtv_output" && pwd)
padtv_build=$(mktemp -d "$padtv_root/build/exo.XXXXXXXX")
cd "$padtv_build"
apt-get source exo=4.20.0-1
cd exo-4.20.0
mkdir -p debian/patches
install -m 644 "$padtv_root/packaging/patches/exo-empty-icon-view.patch" debian/patches/padtv-empty-icon-view.patch
printf '\npadtv-empty-icon-view.patch\n' >> debian/patches/series
python3 - <<'PY'
from pathlib import Path
path = Path('debian/changelog')
path.write_text('''exo (4.20.0-1+0padtv1) trixie; urgency=medium

  * Backport upstream 24b902eb389eecab7b3f8aaefdda4aff7608af9d:
    validate the icon iterator before Home/End selection in empty folders.

 -- PadTV Project <padtv@localhost>  Tue, 24 Nov 2026 08:00:00 +0100

''' + path.read_text())
PY
dpkg-buildpackage -us -uc -b -j"${PADTV_BUILD_JOBS:-8}"
cp -- ../libexo-2-0_4.20.0-1+0padtv1_amd64.deb ../libexo-common_4.20.0-1+0padtv1_all.deb ../exo-utils_4.20.0-1+0padtv1_amd64.deb "$padtv_output/"
echo "Oprava Exo sestavena; zdroj a výsledky: $padtv_build"
