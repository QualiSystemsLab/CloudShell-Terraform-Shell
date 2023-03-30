BASE_10 = 2**10
PREFIX_B = "B"
PREFIX_KB = "KB"
PREFIX_MB = "MB"
PREFIX_GB = "GB"
PREFIX_TB = "TB"
PREFIX_LABELS = [PREFIX_B, PREFIX_KB, PREFIX_MB, PREFIX_GB, PREFIX_TB]


def format_bytes(size, prefix=PREFIX_B):
    prefix_idx = PREFIX_LABELS.index(prefix)
    max_idx = len(PREFIX_LABELS) - 1

    while size // BASE_10 and prefix_idx < max_idx:
        prefix_idx += 1
        size /= BASE_10

    return f"{size:.0f} {PREFIX_LABELS[prefix_idx]}"
