from .s3logging import kogi_print, print_nop

_SLACK = None


def load_slack(slack_id):
    global _SLACK
    try:
        from slackweb import Slack
    except ModuleNotFoundError:
        import os
        os.system('pip install slackweb')
        from slackweb import Slack
    url = f'https://hooks.slack.com/services/{slack_id}'
    try:
        _SLACK = Slack(url)
    except Exception as e:
        kogi_print('Slackに接続できませんでした.', e)


def slack_send(text):
    global _SLACK
    if _SLACK is None:
        kogi_print('slack_idをセットしてください')
        return
    try:
        _SLACK.notify(text=text)
    except Exception as e:
        kogi_print('Slack Error:', e)
