'''
LoggingTool class

The LoggingTool acts a common logging interface.

'''

class LoggingTool(object):
    def __init__(self, options):
        self.options = options
    
    def info(self, message):
        print('info',message)

    def warning(self, message):
        print('warning',message)

    def error(self, message):
        print('error',message)

    def debug(self, message):
        print('debug', message)
