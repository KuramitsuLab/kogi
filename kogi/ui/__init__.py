
from ._google import google_colab
# from ._rmt import TransformWeaver, rmt
from .content import ICON
from .message import kogi_print

if google_colab:
    from .dialog_colab import display_dialog
else:
    try:
        import ipywidgets
        from .dialog_ipywidgets import display_dialog
    except ModuleNotFoundError:
        from .dialog_colab import display_dialog
