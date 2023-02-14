DUP = {}


def DEBUG(*msg):
    msg = ' '.join(str(s) for s in msg)
    if msg not in DUP:
        print('\033[31m[DEBUG]\033[0m', msg)
        DUP[msg] = msg
