"""Fixed application commands. No user text is ever executed as a shell command."""

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class Action:
    title: str
    description: str
    command: tuple[str, ...]
    color: str
    symbol: str


ACTIONS = {
    "browser": Action("Prohlížeč", "Celý web na televizi", (
        "chromium", "--password-store=basic", "--no-first-run", "--no-default-browser-check",
        "--new-window", "--start-fullscreen", "https://www.debian.org/"
    ), "#98a8ff", "globe"),
    "files": Action("Soubory", "Disky, videa a fotografie", ("thunar",), "#ebbd73", "folder"),
    "audio": Action("Zvuk", "Hlasitost a výstup HDMI", ("padtv", "--settings", "audio"), "#82c7a5", "audio"),
    "network": Action("Připojení", "Wi-Fi a kabelová síť", ("padtv", "--settings", "network"), "#8ebce8", "network"),
    "display": Action("Obraz", "Rozlišení a obrazovky", ("padtv", "--settings", "display"), "#ba9beb", "display"),
}

POWER_COMMANDS = {
    "poweroff": ("padtv-systemctl", "power", "poweroff"),
    "reboot": ("padtv-systemctl", "power", "reboot"),
    "suspend": ("padtv-systemctl", "power", "suspend"),
}


def command_for(key: str) -> tuple[str, ...]:
    if key in ACTIONS:
        return ACTIONS[key].command
    if key in POWER_COMMANDS:
        return POWER_COMMANDS[key]
    raise ValueError(f"Neznámá akce: {key}")


def executable_available(key: str) -> bool:
    return shutil.which(command_for(key)[0]) is not None
