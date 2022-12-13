
from .hook import enable_kogi_hook, disable_kogi_hook
from .service import kogi_set, kogi_print, debug_print
from .ui import rmt
import kogi.problem

set = kogi_set
print = kogi_print

enable = enable_kogi_hook
disable = disable_kogi_hook

enable_kogi_hook()
