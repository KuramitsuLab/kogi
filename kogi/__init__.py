
from .settings import kogi_set, kogi_print

set = kogi_set
print = kogi_print

from .hook import enable_kogi_hook, disable_kogi_hook, kogi_register_hook

enable = enable_kogi_hook
disable = disable_kogi_hook

enable_kogi_hook()

from .problem import atcoder_detector, atcoder_judge
kogi_register_hook('atcoder', atcoder_judge, atcoder_detector)

# from .dialog import kogi_ask as ask

from .ui import rmt
