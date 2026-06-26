"""Import every calculator module so its @register decorator runs and the
type becomes available through registry.design()."""

from . import vertical, dipole, efhw  # noqa: F401
