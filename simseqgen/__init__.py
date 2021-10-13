import pathlib

__author__ = """Per Unneberg"""
__email__ = "per.unneberg@scilifelab.se"


__version__ = "undefined"
try:
    from . import _version

    __version__ = _version.version
except ImportError:
    pass


# Package root and data directory paths
ROOT_DIR = pathlib.Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"


from .repo import *  # NOQA
from .generate_references import *  # NOQA
