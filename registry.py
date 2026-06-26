"""Pluggable antenna calculator registry.

Adding a new antenna type means: add data to data/antenna_types.json, write
one calculator function, decorate it with @register("type_key"). Nothing
else (drawing, build notes, tiling) needs to know the type exists ahead of
time -- they all dispatch on AntennaDesign.geometry / .antenna_type.
"""

REGISTRY = {}


def register(antenna_type: str):
    def decorator(fn):
        REGISTRY[antenna_type] = fn
        return fn
    return decorator


def design(antenna_type: str, band: str, lang: str = "en", **kwargs):
    if antenna_type not in REGISTRY:
        raise ValueError(f"Unknown antenna type '{antenna_type}'. Known: {', '.join(REGISTRY)}")
    return REGISTRY[antenna_type](band, lang=lang, **kwargs)
