#!/bin/bash
set -euo pipefail
bridge_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$bridge_root"
cargo build --workspace --release --locked
mkdir -p build/framework build/runtime
bridge_jdk=$(dirname -- "$(dirname -- "$(readlink -f "$(command -v javac)")")")
cc -shared -fPIC -O2 -Wl,-soname,libc.so native/bionic_abi.c -Wl,--no-as-needed -lm -o build/runtime/libpadbridge_bionic_abi.so
cc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Wno-unused-parameter \
    -I"$bridge_jdk/include" -I"$bridge_jdk/include/linux" native/egl.c \
    -o build/runtime/libpadbridge_egl.so $(pkg-config --cflags --libs egl glesv2)
cc -std=c11 -shared -fPIC -O2 -Wall -Wextra -Wno-unused-parameter -Werror=implicit-function-declaration \
    -I"$bridge_jdk/include" -I"$bridge_jdk/include/linux" native/media.c native/audio.c \
    -o build/runtime/libpadbridge_media.so \
    $(pkg-config --cflags --libs libavformat libavcodec libavutil libswscale libswresample sdl2)
find framework/src -name '*.java' -print > build/java-sources.txt
javac --release 8 -encoding UTF-8 -d build/framework @build/java-sources.txt
jar --create --date=2026-11-27T00:00:00Z --file build/runtime/framework.jar -C build/framework .
python3 scripts/fetch-test-tools.py
java -Xmx1g -cp build/test-tools/r8.jar com.android.tools.r8.D8 --min-api 26 --lib build/test-tools/android35.jar --output build/runtime/framework-art.jar build/runtime/framework.jar
cc -std=c11 -O2 -Wall -Wextra -Werror -I"$bridge_jdk/include" -I"$bridge_jdk/include/linux" native/art_vm_probe.c -ldl -o build/runtime/art-vm-probe
mkdir -p build/art-probe/classes
javac --release 8 -d build/art-probe/classes tests/art08/RuntimeProbe.java
java -Xmx512m -cp build/test-tools/r8.jar com.android.tools.r8.D8 --min-api 26 --lib build/test-tools/android35.jar --output build/art-probe/probe.zip build/art-probe/classes/org/padtv/artprobe/*.class
install -m 644 build/art-probe/probe.zip build/runtime/art-probe.apk
mkdir -p build/tools
javac -encoding UTF-8 -cp /usr/share/java/asm-all.jar -d build/tools runtime/tools/ConstructorRepair.java
jar --create --date=2026-11-27T00:00:00Z --file build/runtime/constructor-repair.jar -C build/tools .
python3 runtime/build_api.py build/runtime/host-api.json
install -m 755 target/release/padbridge build/runtime/padbridge
install -m 644 target/release/libpadbridge_native.so runtime/translate.py runtime/resources.py runtime/analyze.py runtime/audio_broker.py runtime/dex_fixes.py runtime/webview.py runtime/certificates.py build/runtime/
install -m 644 runtime/art_runtime.py build/runtime/
