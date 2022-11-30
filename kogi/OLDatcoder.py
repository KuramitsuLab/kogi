
from IPython.core.magic import register_cell_magic
from .OLDatcoder_impl import print, input, _run_judge


@register_cell_magic
def problem(option, code):
    _run_judge(code, option)


@register_cell_magic
def atcoder(option, code):
    _run_judge(code, option)
