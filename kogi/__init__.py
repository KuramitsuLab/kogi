
from .service import kogi_set, debug_print
from .hook import enable_kogi_hook, disable_kogi_hook
from .webui import kogi_print

import kogi.problem

set = kogi_set
print = kogi_print

enable = enable_kogi_hook
disable = disable_kogi_hook

try:
    enable_kogi_hook()
    from kogi.webui.keytype import classroom_login
except:
    pass