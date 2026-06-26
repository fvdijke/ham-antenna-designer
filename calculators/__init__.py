"""Import every calculator module so its @register decorator runs and the
type becomes available through registry.design()."""

from . import (  # noqa: F401
    vertical,
    dipole,
    efhw,
    loop,
    inverted_v,
    ocfd,
    jpole,
    five_eighths,
    edz,
    delta_loop,
    yagi,
    quad,
    moxon,
)
