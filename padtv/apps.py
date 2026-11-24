"""User-installed apps. Defaults are seeded once, never resurrected after removal."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlparse

PACKAGE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+\Z")
APP_ID = re.compile(r"[a-zA-Z0-9_.-]+\Z")


@dataclass(frozen=True)
class UserApp:
    id: str
    title: str
    kind: str
    target: str
    symbol: str = "android"
    color: str = "#a8e4c0"


YOUTUBE = UserApp("youtube", "YouTube", "web", "https://www.youtube.com/", "play", "#ff303f")


def default_data_dir(preview=False):
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "padtv" / ("preview" if preview else "library")


def validate_app(app):
    if not APP_ID.fullmatch(app.id) or app.id in (".", ".."):
        raise ValueError("Neplatný identifikátor aplikace.")
    if not app.title.strip() or len(app.title) > 120:
        raise ValueError("Neplatný název aplikace.")
    if app.kind == "web":
        parsed = urlparse(app.target)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Aplikace musí používat běžnou webovou adresu.")
    elif app.kind == "android":
        if not PACKAGE.fullmatch(app.target):
            raise ValueError("Neplatný název Android balíčku.")
    elif app.kind == "flatpak":
        from padtv_store.catalog import FLATPAK
        if not FLATPAK.fullmatch(app.target):
            raise ValueError("Neplatný identifikátor Flatpak.")
    else:
        raise ValueError("Neznámý typ aplikace.")


class AppLibrary:
    def __init__(self, root):
        self.root = Path(root)
        self.manifests = self.root / "apps"
        self.manifests.mkdir(parents=True, exist_ok=True)
        marker = self.root / "defaults-v1.done"
        if not marker.exists():
            # The marker survives uninstall and application upgrades.
            if not (self.manifests / "youtube.json").exists():
                self.install(YOUTUBE)
            marker.write_text("YouTube was offered on first launch.\n", encoding="utf-8")

    def install(self, app):
        validate_app(app)
        fd, name = tempfile.mkstemp(prefix=".app-", dir=self.manifests)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(asdict(app), stream, ensure_ascii=False, indent=2)
            os.replace(name, self.manifests / f"{app.id}.json")
        finally:
            Path(name).unlink(missing_ok=True)

    def list(self):
        items = []
        for path in self.manifests.glob("*.json"):
            try:
                app = UserApp(**json.loads(path.read_text(encoding="utf-8")))
                validate_app(app)
                if path.stem == app.id:
                    items.append(app)
            except (OSError, ValueError, TypeError):
                continue
        return sorted(items, key=lambda app: (app.id != "youtube" and app.target != "com.google.android.youtube.tv", app.title.casefold()))

    def remove(self, app, remove_data=False):
        validate_app(app)
        # Android packages must first be removed successfully by Waydroid.
        if remove_data and app.kind == "web":
            profile = self.root / "profiles" / app.id
            if (self.root / "profiles").is_symlink():
                raise ValueError("Adresář profilů nesmí být odkaz mimo knihovnu.")
            if profile.is_symlink():
                profile.unlink()
            elif profile.exists():
                parent = (self.root / "profiles").resolve()
                if profile.resolve().parent != parent:
                    raise ValueError("Neplatná cesta dat aplikace.")
                shutil.rmtree(profile)
        (self.manifests / f"{app.id}.json").unlink(missing_ok=True)

    def command(self, app):
        validate_app(app)
        if app.kind == "android":
            return ("padtv-android", "launch", app.target)
        if app.kind == "flatpak":
            return ("flatpak", "run", app.target)
        profile = (self.root / "profiles" / app.id).resolve()
        return ("chromium", f"--user-data-dir={profile}", "--password-store=basic",
                "--no-first-run", "--no-default-browser-check", "--new-window", "--start-fullscreen", f"--app={app.target}")
