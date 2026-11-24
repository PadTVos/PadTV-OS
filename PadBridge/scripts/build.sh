#!/bin/bash
set -euo pipefail
bridge_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$bridge_root"
cargo build --workspace --release --locked
mkdir -p build/framework build/runtime
find framework/src -name '*.java' -print > build/java-sources.txt
javac --release 8 -encoding UTF-8 -d build/framework @build/java-sources.txt
jar --create --file build/runtime/framework.jar -C build/framework .
python3 runtime/build_api.py build/runtime/host-api.json
install -m 755 target/release/padbridge build/runtime/padbridge
install -m 644 target/release/libpadbridge_native.so runtime/translate.py runtime/resources.py runtime/analyze.py build/runtime/
