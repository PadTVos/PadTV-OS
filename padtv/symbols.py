"""User-supplied PadTV V6 SVG artwork, rendered once for Qt's raster cache."""
from pathlib import Path
from PyQt6.QtGui import QPixmap

ALIASES = {'globe':'internet','folder':'files','audio':'sound','network':'wifi',
           'user':'account','manage':'apps','system':'info'}
_cache = {}

def symbol_pixmap(name):
    name = ALIASES.get(name, name)
    if name not in _cache:
        _cache[name] = QPixmap(str(Path(__file__).parent/'assets/icons-v6'/(name+'.png')))
    return _cache[name]
