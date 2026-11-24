#!/bin/bash
set -euo pipefail
padtv_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
padtv_output=${1:-"$padtv_root/dist"}
for tool in dpkg-deb python3; do
    command -v "$tool" >/dev/null || { echo "Chybí $tool." >&2; exit 1; }
done
mkdir -p -- "$padtv_output"
padtv_output=$(cd -- "$padtv_output" && pwd)
padtv_temp=$(mktemp -d)
trap 'rm -rf -- "$padtv_temp"' EXIT
padtv_stage="$padtv_temp/session"
install -d "$padtv_stage/DEBIAN" "$padtv_stage/usr/share/padtv/padtv" \
    "$padtv_stage/usr/bin" "$padtv_stage/etc/padtv/labwc" \
    "$padtv_stage/usr/share/padtv/padtv/assets" "$padtv_stage/usr/lib/padtv" \
    "$padtv_stage/usr/lib/systemd/user" "$padtv_stage/usr/share/padtv/android"
install -m 644 "$padtv_root/packaging/control" "$padtv_stage/DEBIAN/control"
install -m 755 "$padtv_root/packaging/postinst" "$padtv_root/packaging/prerm" "$padtv_stage/DEBIAN/"
install -m 644 "$padtv_root"/padtv/*.py "$padtv_stage/usr/share/padtv/padtv/"
install -d "$padtv_stage/usr/share/padtv/padtv_store" "$padtv_stage/usr/share/padtv/catalog"
install -m 644 "$padtv_root"/padtv_store/*.py "$padtv_stage/usr/share/padtv/padtv_store/"
install -m 644 "$padtv_root/catalog/apps.json" "$padtv_stage/usr/share/padtv/catalog/"
install -d "$padtv_stage/usr/share/xdg-desktop-portal"
install -m 644 "$padtv_root/packaging/portals.conf" "$padtv_stage/usr/share/xdg-desktop-portal/padtv-portals.conf"
install -m 755 "$padtv_root/packaging/padtv" "$padtv_root/packaging/padtv-session" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/padtv-android" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/padtv-android-init" "$padtv_stage/usr/lib/padtv/"
install -m 644 "$padtv_root/packaging/padtv-tv.xml" "$padtv_stage/usr/share/padtv/android/"
install -m 644 "$padtv_root"/packaging/padtv-android-*.service "$padtv_stage/usr/lib/systemd/user/"
install -m 644 "$padtv_root/packaging/padtv-audio-restore.service" "$padtv_stage/usr/lib/systemd/user/"
install -m 755 "$padtv_root/packaging/padtv-volume" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/padtv-system-settings" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/padtv-android-display" "$padtv_stage/usr/lib/padtv/"
install -m 755 "$padtv_root/packaging/padtv-session-cleanup" "$padtv_stage/usr/lib/padtv/"
install -m 644 "$padtv_root/packaging/padtv-shell.service" "$padtv_root/packaging/padtv-polkit.service" "$padtv_root/packaging/padtv-session.target" "$padtv_stage/usr/lib/systemd/user/"
install -m 644 "$padtv_root"/padtv/assets/*.png "$padtv_stage/usr/share/padtv/padtv/assets/"
install -d "$padtv_stage/usr/share/padtv/padtv/assets/icons-v6"
install -m 644 "$padtv_root"/padtv/assets/icons-v6/* "$padtv_stage/usr/share/padtv/padtv/assets/icons-v6/"
install -m 644 "$padtv_root/packaging/greetd.toml" "$padtv_stage/etc/padtv/"
install -m 644 "$padtv_root/packaging/labwc/rc.xml" "$padtv_root/packaging/labwc/environment" "$padtv_stage/etc/padtv/labwc/"
install -m 755 "$padtv_root/packaging/labwc/autostart" "$padtv_stage/etc/padtv/labwc/"
install -d "$padtv_stage/usr/lib/systemd/system" "$padtv_stage/usr/share/polkit-1/rules.d" \
    "$padtv_stage/etc/chromium/policies/managed" "$padtv_stage/usr/share/plymouth/themes/padtv"
install -m 644 "$padtv_root/packaging/padtv.service" "$padtv_stage/usr/lib/systemd/system/"
install -m 644 "$padtv_root/packaging/49-padtv.rules" "$padtv_stage/usr/share/polkit-1/rules.d/"
install -m 644 "$padtv_root/packaging/chromium-policy.json" "$padtv_stage/etc/chromium/policies/managed/padtv.json"
install -m 644 "$padtv_root/packaging/plymouth/"* "$padtv_stage/usr/share/plymouth/themes/padtv/"
install -m 644 "$padtv_root/padtv/assets/logo.png" "$padtv_stage/usr/share/plymouth/themes/padtv/"
find "$padtv_stage/etc" -type f -printf '/etc/%P\n' > "$padtv_stage/DEBIAN/conffiles"
padtv_version=$(PYTHONPATH="$padtv_root" python3 -c 'from padtv import __version__; print(__version__)')
dpkg-deb --root-owner-group --build "$padtv_stage" "$padtv_output/padtv-session_${padtv_version}_all.deb"

padtv_stage="$padtv_temp/core"
install -d "$padtv_stage/DEBIAN" "$padtv_stage/usr/lib/padtv-core/padtv_core" \
    "$padtv_stage/usr/bin" "$padtv_stage/usr/lib/padtv" "$padtv_stage/usr/lib/systemd/system" \
    "$padtv_stage/usr/share/dbus-1/system.d" "$padtv_stage/usr/share/polkit-1/actions" "$padtv_stage/usr/share/polkit-1/rules.d"
install -m 644 "$padtv_root/packaging/core/control" "$padtv_stage/DEBIAN/"
install -m 755 "$padtv_root/packaging/core/postinst" "$padtv_root/packaging/core/postrm" "$padtv_stage/DEBIAN/"
install -m 644 "$padtv_root"/padtv_core/*.py "$padtv_stage/usr/lib/padtv-core/padtv_core/"
install -m 644 "$padtv_root/packaging/core/os-release" "$padtv_stage/usr/lib/padtv-core/"
install -m 755 "$padtv_root/packaging/core/padtv-systemctl" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/padtv-account" "$padtv_stage/usr/lib/padtv/"
install -m 755 "$padtv_root/packaging/core/padtv-active-session" "$padtv_stage/usr/lib/padtv/"
install -m 644 "$padtv_root/packaging/padtv-account.service" "$padtv_root/packaging/core/padtv-system.service" "$padtv_stage/usr/lib/systemd/system/"
install -m 644 "$padtv_root/packaging/core/org.padtv.System1.conf" "$padtv_stage/usr/share/dbus-1/system.d/"
install -m 644 "$padtv_root/packaging/core/org.padtv.system.policy" "$padtv_stage/usr/share/polkit-1/actions/"
install -m 644 "$padtv_root/packaging/core/48-padtv-core.rules" "$padtv_stage/usr/share/polkit-1/rules.d/"
dpkg-deb --root-owner-group --build "$padtv_stage" "$padtv_output/padtv-core_${padtv_version}_all.deb"

padtv_stage="$padtv_temp/installer"
install -d "$padtv_stage/DEBIAN" "$padtv_stage/usr/bin" "$padtv_stage/usr/lib/padtv" \
    "$padtv_stage/etc/calamares/modules" "$padtv_stage/etc/calamares/branding/padtv" \
    "$padtv_stage/usr/lib/calamares/modules/padtv-finalize" "$padtv_stage/usr/share/polkit-1/rules.d"
install -m 644 "$padtv_root/packaging/installer/control" "$padtv_stage/DEBIAN/"
install -m 755 "$padtv_root/packaging/installer/padtv-installer" "$padtv_stage/usr/bin/"
install -m 755 "$padtv_root/packaging/installer/padtv-install-gui" "$padtv_stage/usr/lib/padtv/"
install -m 644 "$padtv_root/packaging/installer/49-padtv-installer.rules" "$padtv_stage/usr/share/polkit-1/rules.d/"
install -m 644 "$padtv_root/packaging/installer/settings.conf" "$padtv_stage/etc/calamares/"
install -m 644 "$padtv_root/packaging/installer/modules/"* "$padtv_stage/etc/calamares/modules/"
install -m 644 "$padtv_root/packaging/installer/branding/"* "$padtv_root"/padtv/assets/*.png "$padtv_stage/etc/calamares/branding/padtv/"
install -m 644 "$padtv_root/packaging/installer/padtv-finalize/main.py" \
    "$padtv_root/packaging/installer/padtv-finalize/module.desc" "$padtv_stage/usr/lib/calamares/modules/padtv-finalize/"
find "$padtv_stage/etc" -type f -printf '/etc/%P\n' > "$padtv_stage/DEBIAN/conffiles"
dpkg-deb --root-owner-group --build "$padtv_stage" "$padtv_output/padtv-installer_${padtv_version}_all.deb"
