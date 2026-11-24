#!/bin/bash
set -euo pipefail
bridge_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
bridge_output=${1:-"$bridge_root/build"}
mkdir -p "$bridge_output"
bridge_output=$(cd "$bridge_output" && pwd)
bash "$bridge_root/scripts/build.sh"
python3 "$bridge_root/tests/build_fixtures.py"
bridge_stage=$(mktemp -d)
trap 'rm -rf -- "$bridge_stage"' EXIT
install -d "$bridge_stage/DEBIAN" "$bridge_stage/usr/bin" "$bridge_stage/usr/lib/padbridge" "$bridge_stage/usr/share/doc/padbridge"
install -m 644 "$bridge_root/packaging/control" "$bridge_stage/DEBIAN/"
install -m 755 "$bridge_root/build/runtime/padbridge" "$bridge_stage/usr/bin/"
install -m 644 "$bridge_root/build/runtime/"*.jar "$bridge_root/build/runtime/"*.so "$bridge_root/runtime/translate.py" "$bridge_stage/usr/lib/padbridge/"
install -m 644 "$bridge_root/README.md" "$bridge_root/THIRD_PARTY.md" "$bridge_root/LICENSE" "$bridge_stage/usr/share/doc/padbridge/"
install -d "$bridge_stage/usr/share/padbridge/examples"
install -m 644 "$bridge_root/build/fixtures/basic.apk" "$bridge_stage/usr/share/padbridge/examples/"
dpkg-deb --root-owner-group --build "$bridge_stage" "$bridge_output/padbridge_0.1.0_amd64.deb"
