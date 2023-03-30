from __future__ import annotations

import attr

BASE_10 = 2**10
BASE_SI = 1000

PREFIX_B = "B"
PREFIX_KB = "KB"
PREFIX_MB = "MB"
PREFIX_GB = "GB"
PREFIX_TB = "TB"
BYTES_PREFIX_LABELS = [PREFIX_B, PREFIX_KB, PREFIX_MB, PREFIX_GB, PREFIX_TB]

PREFIX_HZ = "Hz"
PREFIX_KHZ = "kHz"
PREFIX_MHZ = "MHz"
PREFIX_GHZ = "GHz"
HERTZ_PREFIX_LABELS = [PREFIX_HZ, PREFIX_KHZ, PREFIX_MHZ, PREFIX_GHZ]


def _format_units(size, prefix, prefixes, unit_step):
    prefix_idx = prefixes.index(prefix)

    while size // unit_step and prefix_idx < len(prefixes) - 1:
        prefix_idx += 1
        size /= unit_step

    return f"{size:.2f} {prefixes[prefix_idx]}"


def format_bytes(size, prefix=PREFIX_B):
    return _format_units(
        size=size, prefix=prefix, prefixes=BYTES_PREFIX_LABELS, unit_step=BASE_10
    )


def format_hertz(size, prefix=PREFIX_HZ):
    return _format_units(
        size=size, prefix=prefix, prefixes=HERTZ_PREFIX_LABELS, unit_step=BASE_SI
    )


@attr.s(auto_attribs=True)
class UsageInfo:
    capacity: str
    used: str
    free: str
    used_percentage: str

    def to_dict(self) -> dict[str, str]:
        return attr.asdict(self)
