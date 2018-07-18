'''
LoggingTool class

The LoggingTool acts a common logging interface.

'''
import logging
import sys

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

        self.handlers = []
        self.name = name
        self.logger = self.get_logger(name)

        # load options
        self.level = self.get_option(options, 'level')
        self.outfile_opts = self.get_option(options, 'outfile')
        self.stdout_opts = self.get_option(options, 'stdout')
        self.stderr_opts = self.get_option(options, 'stderr')
        self.format = self.get_option(options, 'format')

        # set level
        self.set_level(self.level)

        # add handlers
        if len(self.logger.handlers) > 0:
            self.handlers = self.logger.handlers
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
        self.set_format(self.format)
        self.debug('{} initialized'.format(self))

    @staticmethod
    def get_logger(name):
        ''' Return python Logger object with name '''
        if name is None:
            return logging.getLogger('reco3d')
        else:
            return logging.getLogger(name)

    @classmethod
    def get_option(cls, options, key):
        ''' Grab option from OptionsTool. If it doesn't exist, use default '''
        if options[key] is None:
            return cls.default_opts[key]
        else:
            return options[key]

    def add_filehandler(self, filename, level):
        ''' Add a FileHandler to current handlers list '''
        fh = logging.FileHandler(filename)
        fh.setLevel(self.level_lookup[level])
        self.handlers += [fh]
        self.logger.addHandler(fh)

    def add_streamhandler(self, stream, level):
        ''' Add a StreamHandler to current handlers list '''
        sh = logging.StreamHandler(stream)
        sh.setLevel(self.level_lookup[level])
        self.handlers += [sh]
        self.logger.addHandler(sh)

    def set_format(self, format):
        ''' Create a formatter and apply to handlers '''
        self.formatter = logging.Formatter(format)
        for handler in self.logger.handlers:
            handler.setFormatter(self.formatter)

    def set_level(self, level):
        ''' Set logger level '''
        self.logger.setLevel(self.level_lookup[level])

    def info(self, message):
        #print('info',message)
        self.logger.info(str(message))

    def warning(self, message):
        #print('warning',message)
        self.logger.warning(str(message))

    def error(self, message):
        #print('error',message)
        self.logger.error(str(message))

    def debug(self, message):
        #print('debug', message)
        self.logger.debug(str(message))

    def critical(self, message):
        #print('critical', message)
        self.logger.critical(str(message))

