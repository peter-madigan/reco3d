'''
LoggingTool class

The LoggingTool acts a common logging interface.
options:
 - `"level"`: log level. Can be any of `["debug","info","warning","error","critical"]`, but higher than
 `"error"` is not recommended.
 - `"outfile"`: tuple of `(<enable file logging>, <file log level>, <file path>)`
 - `"stdout"`: tuple of `(<enable stdout logging>, <stdout log level>)`
 - `"stderr"`: tuple of `(<enable stderr logging>, <stderr log level>)`
 - `"format"`: log message string (see python logging module for formatting)

Each LoggingTool object provides access to the following logging methods:
 - `debug()` lowest level logging (whatever the developer thinks is useful at some point in time)
 - `info()` higher level logging (stage, event loop progress, etc)
 - `warning()` log things that may cause issues (two loggers are initialized with the same name, etc)
 - `error()` log things that are going to cause issues (accessing write methods of read-only objects, missing arguments etc)
 - `critical()` log things that requires the process to stop

'''
import logging
import sys
from timeit import default_timer

def timed(method):
    ''' Decorator for measuring execution times '''
    def timed_method(*args, **kwargs):
        ti = default_timer()
        result = method(*args, **kwargs)
        tf = default_timer()
        if tf - ti > 0.25:
            print('{}: {}'.format(str(method), tf - ti))
        return result
    return timed_method

class LoggingTool(object):
    # default formatting string
    default_format = '%(asctime)s %(levelname)s\t%(name)s: %(message)s'

    # list of required options (raises error if not found)
    req_opts = []
    # list of option arguments and default values (for initialization)
    default_opts = {
        # basic log level : level
        'level' : 'debug',
        # output file handler : [enabled?, log level, filename]
        'outfile' : [False, 'debug', '.log'],
        # stdout stream handler : [enabled?, log level]
        'stdout' : [True, 'info'],
        # stderr stream handler : [enabled?, log level]
        'stderr' : [False, 'error'],
        # formatter : format string
        'format' : default_format,
        }

    level_lookup = {
        'debug' : logging.DEBUG,
        'info' : logging.INFO,
        'warning' : logging.WARNING,
        'error' : logging.ERROR,
        'critical' : logging.CRITICAL
        }

    def __init__(self, options, name=None):
        self.options = options
        self.options.check_req(self.req_opts)
        self.options.set_default(self.default_opts)

        self.handlers = []
        self.name = name
        self._logger = self.get_logger(name)

        # load options
        self.level = self.options['level']
        self.outfile_opts = self.options['outfile']
        self.stdout_opts = self.options['stdout']
        self.stderr_opts = self.options['stderr']
        self.log_format = self.options['format']

        # set level
        self.set_level(self.level)

        # add handlers
        if self._logger.handlers:
            self.handlers = self._logger.handlers
            self.warning('Logger already initialized - skipping handler init')
            # if handlers already initialized, skip handler initialization
        else:
            if self.outfile_opts[0]: # enable?
                self.add_filehandler(self.outfile_opts[2], self.outfile_opts[1])
            if self.stdout_opts[0]: # enable?
                self.add_streamhandler(sys.stdout, self.stdout_opts[1])
            if self.stderr_opts[0]: # enable?
                self.add_streamhandler(sys.stderr, self.stderr_opts[1])

        # set format
        self.set_format(self.log_format)
        self.debug('{} initialized'.format(self))

    @staticmethod
    def get_logger(name):
        ''' Return python Logger object with name '''
        if name is None:
            return logging.getLogger('reco3d')
        return logging.getLogger(name)

    def add_filehandler(self, filename, level):
        ''' Add a FileHandler to current handlers list '''
        fh = logging.FileHandler(filename)
        fh.setLevel(self.level_lookup[level])
        self.handlers += [fh]
        self._logger.addHandler(fh)

    def add_streamhandler(self, stream, level):
        ''' Add a StreamHandler to current handlers list '''
        sh = logging.StreamHandler(stream)
        sh.setLevel(self.level_lookup[level])
        self.handlers += [sh]
        self._logger.addHandler(sh)

    def set_format(self, log_format):
        ''' Create a formatter and apply to handlers '''
        self.formatter = logging.Formatter(log_format)
        for handler in self.handlers:
            handler.setFormatter(self.formatter)

    def set_level(self, level):
        ''' Set logger level '''
        self._logger.setLevel(self.level_lookup[level])

    def info(self, message):
        #print('info',message)
        self._logger.info(str(message))

    def warning(self, message):
        #print('warning',message)
        self._logger.warning(str(message))

    def error(self, message):
        #print('error',message)
        self._logger.error(str(message))

    def debug(self, message):
        #print('debug', message)
        self._logger.debug(str(message))

    def critical(self, message):
        #print('critical', message)
        self._logger.critical(str(message))
