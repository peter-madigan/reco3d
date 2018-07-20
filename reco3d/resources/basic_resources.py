from reco3d.tools.logging import LoggingTool
from reco3d.converters.basic_converters import Converter

class Resource(object):
    req_opts = [] # list of required options
    default_opts = {} # dict of options with default values

    def __init__(self, options):
        self.options = options
        self.options.check_req(self.req_opts)
        self.options.set_default(self.default_opts)
        self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
        self._read_queue = {} # pre-loaded data available to processes (refreshed every call to run() or start())
        self._write_queue = {} # data to be written once a condition has been met
        self._stack = {} # live data (typically updated every event loop and is modified by
                         # processes during event loop)
        self._stack_hold = {} # signal to resource to keep stack for another iteration
        self._cache = {} # passive data (speed up access to external resources, lookup only)
        self.logger.debug('{} initialized'.format(self))

    def config(self):
        # do stuff
        pass

    def start(self):
        # open files
        # fill cache
        # queue up data (if needed)
        pass

    def run(self):
        # write write queue (if necessary)
        # clean up cache
        # refresh stack
        for dtype in self._stack.keys():
            if dtype in self._stack_hold and self._stack_hold[dtype]:
                pass
            else:
                self.clear(dtype)
        # prepare read queue
        pass

    def continue_run(self):
        # return True unless the event loop should be ended (e.g. EOF reached)
        return True

    def finish(self):
        # do any finalization
        # flush buffers
        pass

    def cleanup(self):
        # close files
        pass

    def read(self, dtype, n=1):
        # fetch from read queue
        return None

    def write(self, obj):
        # put obj in write queue
        pass

    def get(self, loc, id=None):
        # return object at loc that matches id, else return none
        return None

    def set(self, loc, obj):
        # attempt to store obj at loc, return True if successful, False if not
        return False

    def read_queue_dtypes(self):
        # fetch a list of all data types in read queue
        return self._read_queue.keys()

    def stack_dtypes(self):
        # fetch a list of all data types in stack
        return self._stack.keys()

    def write_queue_dtypes(self):
        # fetch a list of all data types in write_queue
        return self._write_queue.keys()

    def pop(self, dtype, n=1):
        # grab object from active stack, else return None
        if dtype in self._stack.keys():
            if n == -1:
                obj = self._stack[dtype][:]
                self._stack[dtype] = []
                return obj
            elif n == 1:
                obj = self._stack[dtype][-1]
                self._stack[dtype] = self._stack[dtype][:-1]
                return obj
            else:
                obj = self._stack[dtype][-n:]
                self._stack[dtype] = self._stack[dtype][:-n]
                return obj
        return None

    def push(self, obj):
        # put object in active stack
        if obj is None:
            return
        if isinstance(obj, list):
            dtype = type(obj[0])
            if dtype in self._stack.keys():
                self._stack[dtype] += obj
            else:
                self._stack[dtype] = obj
        else:
            dtype = type(obj)
            if dtype in self._stack.keys():
                self._stack[dtype].append(obj)
            else:
                self._stack[dtype] = [obj]

    def peek(self, dtype, n=1):
        # grab object from active stack, leaving stack intact
        if dtype in self._stack.keys():
            if n == -1:
                return self._stack[dtype][:].copy()
            elif n == 1:
                return self._stack[dtype][-1]
            else:
                return self._stack[dtype][-n:].copy()
        return None

    def clear(self, dtype=None):
        # refresh active stack (occurs automatically every call to run() unless there is a stack_hold)
        if dtype is None:
            self._stack = {}
        elif dtype in self._stack.keys():
            del self._stack[dtype]
        else:
            pass

    def hold(self, dtype):
        # request hold on stack refresh, return false if not possible
        self._stack_hold[dtype] = True
        return self._stack_hold[dtype]
