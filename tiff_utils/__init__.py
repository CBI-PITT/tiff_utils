try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"


from tiff_utils import tiff
