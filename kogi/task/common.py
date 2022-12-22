from kogi.service import debug_print, check_awake
from kogi.ui.render import Doc
from kogi.ui.wait_and_ready import wait_for_ready_doc


def status_message(status):
    return wait_for_ready_doc(check_ready_fn=check_awake)
    # return '@robot:言語モデルをロード中！ 待たせてごめんね！'
