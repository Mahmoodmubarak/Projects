
def dbg_console(msg):
    if DEBUG:
        t =  datetime.now().strftime("%d-%m-%y  %H:%M:%S")
        prefix = '['+t+'] '
        print(prefix+msg)


def dbg(msg):
    if DEBUG:
        t =  datetime.now().strftime("%d-%m-%y  %H:%M:%S")
        prefix = '['+t+'] '
        return prefix+msg