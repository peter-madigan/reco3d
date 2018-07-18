from reco3d.tools.logging import LoggingTool

class Converter(object):
    req_opts = [] # list of required options (raises error)
    default_opts = {} # list of option arguments with default values

    def __init__(self, options):
        self.options = options
        self.options.check_req(self.req_opts)
        self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
        self.logger('{} initialized'.format(self))

    def open(self):
        # open converter (typically occurs during config phase)
        pass

    def close(self):
        # close converter (typically occurs during cleanup phase)
        pass

    def read(self, loc, id=None):
        # looking at loc, return objects that match id
        return None

    def write(self, data, loc=None):
        # write data to location. If None specified, append to end of dataset
        # return True if successful, False if not
        return False


