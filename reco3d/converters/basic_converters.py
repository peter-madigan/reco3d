'''
This module contains the base class for Converter-type objects

Converters handle data IO to external services such as file formats, guis, etc, and are
instantiated by Resources.

Each Converter class has the following methods and attributes:
 - a `req_opts` attribute that is a list of required option keys, if an OptionsTool is passed into
 the Converter without all of the keys listed in `req_opts` a RuntimeError is raised
 - a `default_opts` attribute that is a dict of all options with default values
 - an `open()` method that can be called by the parent Resource during the config stage
 - a `close()` method that can be called by the parent Resource during the cleanup stage
 - a `read(dtype, loc=None)` method to read data from external service*
 - a `write(data, loc=None)` method to write data to the external service*

Inheritance from the basic_converters.Converter class provides:
 - a `logger` object of type `LoggingTool`
 - an `options` object of type `OptionsTool`

*Note: There is no specification for the `loc` of data, however the mapping should be clearly
documented in the implementation and unique for each data object.

'''
from reco3d.tools.logging import LoggingTool

class Converter(object):
    req_opts = [] # list of required options (raises error)
    default_opts = {} # list of option arguments with default values

    def __init__(self, options):
        self.options = options
        self.options.check_req(self.req_opts)
        self.options.set_default(self.default_opts)
        self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)

    def open(self):
        ''' Open converter (typically occurs during config phase) '''
        pass

    def close(self):
        ''' Close converter (typically occurs during cleanup phase) '''
        pass

    def read(self, dtype, loc=None):
        ''' Looking at `loc`, return objects that match type. If `loc` is None, return "next" object '''
        return None

    def write(self, data, loc=None):
        '''
        Write data to location. If None specified, append to end of dataset
        Return True if successful, False if not
        '''
        return False


