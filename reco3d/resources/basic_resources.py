'''
This module contains the base Resource class

Resources handle the storage and access of data for Processes.

Each Resource class has the following methods and attributes:
 - a `req_opts` attribute that is a list of required option keys. If an OptionsTool is passed into
 the Resource with all of these keys, a RuntimeError is raised
 - a `default_opts` attribute that is a dict of all options with default values
 - a `config()` method. Typically, this sets up configuration attributes and creates Converter objects
 - a `start()` method. Typically, this opens Converter objects and pre-loads data before the event loop
 - a `continue_run()` method that returns False if the event loop should be halted
 - a `run()` method that is executed every event loop
 - a `finish()` method. Typically, this flushes write data to Converter objects
 - a `cleanup()` method. Typically, this closes Converter objects
 - a `get()` and `set()` method for accessing static data (not implemented in basic_resources.Resource)
 - a `read()` and `write()` method for accessing Converter data (implemented in basic_resources.Resource)
 - a `pop()`, `push()`, `peek()`, and `purge()` method for accessing stack data (implemented in basic_resources.Resource)
 - a `preserve()` method for keeping stack data for an additional event loop (implemented in basic_resources.Resource)
 - a `read_queue_dtypes()`, `write_queue_dtypes()`, and `stack_dtypes()` method for accessing data types within respective
 objects

Inheritance from the basic_resource.Resource class provides:
 - a `logger` object of type `LoggingTool`
 - an `options` object of type `OptionsTool`
 - a `_read_queue` dict that provides data to the `read()` method. The keys in this dict are datatypes
 and the values are lists of data objects
 - a `_write_queue` dict that is filled by the `write()` method. The keys in this dict are datatypes
 and the values are lists of data objects
 - a `_stack` dict that is accessed via `pop()`, `push()`, `peek()`, and `purge()` methods. The keys in this dict
 are datatypes and the values are lists of data objects. The each datatype list is cleared after calling
 `Resource.run()` unless `_stack_hold[<dtype>]` is `True`.
 - a `_stack_hold` dict that is accessed via the `preserve()` method. The keys in this dict are datatypes
 and the values are T/F depending on if a stack hold has been placed for this event loop iteration
 - a `_cache` dict that can be used to provide quicker data access. There is no standardization of the
 keys and value for this object

'''

from reco3d.tools.logging import LoggingTool

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
        pass

    def start(self):
        pass

    def run(self):
        '''
        Resource run() method refreshes stack unless there is a stack hold in place
        Holds expire after every call to run

        Suggested uses of the run() method in inheriting classes could be writing the write queue, cleaning up
        the cache, or prepare read queue data

        '''
        # refresh the stack
        stacks_to_clear = []
        for dtype in self._stack.keys():
            if dtype in self._stack_hold and self._stack_hold[dtype]:
                pass
            else:
                stacks_to_clear += [dtype]
            self._stack_hold[dtype] = False
        for dtype in stacks_to_clear:
            self.purge(dtype)

    def continue_run(self):
        '''
        Return false if the event loop should be ended (e.g. the EOF is reached)
        This method is checked at the end of each event loop iteration
        '''
        return True

    def finish(self):
        '''
        Finalize data after event loop (e.g. flush data to external resources)
        '''
        pass

    def cleanup(self):
        pass

    def read(self, dtype, n=1):
        ''' Fetch data from read queue '''
        if not dtype in self._read_queue:
            return None
        if not self._read_queue[dtype]:
            return None
        if n == -1:
            return_objs = self._read_queue[dtype]
            self._read_queue[dtype] = []
            return return_objs
        elif n == 1:
            return_obj = self._read_queue[dtype][0]
            self._read_queue[dtype] = self._read_queue[dtype][1:]
            return return_obj
        elif n > 0:
            return_objs = self._read_queue[dtype][:n]
            self._read_queue[dtype] = self._read_queue[dtype][n:]
            return return_objs
        return None

    def write(self, obj):
        ''' Put object into write queue '''
        if obj is None:
            return
        if not obj:
            return
        if isinstance(obj, list):
            dtype = type(obj[0])
            if not dtype in self._write_queue:
                self._write_queue[dtype] = obj
            else:
                self._write_queue[dtype] += obj
        else:
            dtype = type(obj)
            if not dtype in self._write_queue:
                self._write_queue[dtype] = [obj]
            else:
                self._write_queue[dtype] += [obj]

    def get(self, loc, dtype=None):
        ''' Return object at loc that matches datatype, else return none '''
        return None

    def set(self, loc, obj):
        ''' Attempt to store obj at loc, return True if successful, False if not '''
        return False

    def read_queue_dtypes(self):
        ''' Fetch a list of all data types in read queue '''
        return self._read_queue.keys()

    def stack_dtypes(self):
        ''' Fetch a list of all data types in stack '''
        return self._stack.keys()

    def write_queue_dtypes(self):
        ''' Fetch a list of all data types in write_queue '''
        return self._write_queue.keys()

    def pop(self, dtype, n=1):
        '''
        Grab object from active stack, else return None
        If grabbing multiple objects, a list of objects is returned with an order
        as though you had called [pop(dtype) for _ in range(n)]
        '''
        if dtype in self._stack.keys():
            if n == -1:
                obj = reversed(self._stack[dtype][:])
                self._stack[dtype] = []
                return list(obj)
            elif n == 1:
                obj = self._stack[dtype][-1]
                self._stack[dtype] = self._stack[dtype][:-1]
                return obj
            else:
                obj = reversed(self._stack[dtype][-n:])
                self._stack[dtype] = self._stack[dtype][:-n]
                return list(obj)
        return None

    def push(self, obj):
        ''' Put object in active stack '''
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
        ''' Grab object from active stack, leaving stack intact '''
        if dtype in self._stack.keys():
            if n == -1:
                return list(reversed(self._stack[dtype][:].copy()))
            elif n == 1:
                return self._stack[dtype][-1]
            else:
                return list(reversed(self._stack[dtype][-n:].copy()))
        return None

    def purge(self, dtype=None):
        ''' Refresh active stack (occurs automatically every call to run() unless there is a stack_hold) '''
        if dtype is None:
            self._stack = {}
        elif dtype in self._stack.keys():
            del self._stack[dtype]
        else:
            pass

    def preserve(self, dtype):
        ''' Request hold on stack refresh, return false if not possible '''
        self._stack_hold[dtype] = True
        return self._stack_hold[dtype]
