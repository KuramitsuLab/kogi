from kogi.service import debug_print, check_awake
from kogi.ui.render import Doc
from kogi.ui.wait_and_ready import wait_for_ready_doc


def status_message(status):
    doc = wait_for_ready_doc(check_ready_fn=check_awake)
    doc.set_mention('@ta')
    return doc
