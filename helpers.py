class Printer(object):
    def __init__(self):
        self.on = True

    def __call__(self, message, *stuff):
        if self.on:
            print(message.format(*stuff))
        return stuff[0]
