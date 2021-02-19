import platform


class OS:
    """A simple wrapper to handle OS-specific switches.

    Attributes:
        is_windows: A boolean of whether the current system is MS Windows.
        is_nix: A boolean of whether the current system is *nix (any Linux).
        file_uri_prefix: A string to be used as the default prefix for URIs
            which point to local files on the system.

    """

    is_windows: bool = platform.system() == 'Windows'
    is_nix: bool = not is_windows

    file_uri_prefix: str = 'file:///' if is_windows else 'file://'
