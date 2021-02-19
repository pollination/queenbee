import platform


class OS:
    """A simple wrapper to handle OS-specific switches."""

    is_windows: bool = platform.system() == 'Windows'
    is_nix: bool = platform.system() == 'Linux'

    file_uri_prefix: str = 'file:///' if is_windows else 'file://'
