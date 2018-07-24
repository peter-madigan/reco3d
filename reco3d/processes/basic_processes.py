'''
This module contains the base class for Process-type objects

Processes perform calculations on data accessed via Resources. After configuration, object attributes
should not change.

Each Process class has the following:
 - a `req_opts` attribute that is a list of required option keys, if an OptionsTool is passed into the
 Converter without all of the keys listed in `req_opts` a RuntimeError is raised
 - a `default_opts` attribute that is a dict of all options with default values
 - a `opt_resources` attribute that is a dict of optional resources used by process. Keys are the keyword
 name of the resource (used when creating the process and access to the resource via the resource manager)
 and values are lists of Resource class names that can be used (None enables any resource type)
 - a `req_resources` attribute that is a dict of required resources used by the process. Keys are the keyword
 name of the resource (used when creating the process and access to the resource via the resource manager)
 and values are lists of Resource class names that can be used (None enables any resource type). If any of
 these resources are not specified upon creation, a RuntimeError will be raised during the config stage.
 - the `start()`, `run()`, `continue_run()`, `finish()`, and `cleanup()` methods are not implemented by the
 basic_processes.Process class
 - the `config()` method checks for required resources and resource types, additional functionality may be
 implemented in inheriting classes

Inheritance from the basic_processes.Process provides:
 - a `logger` object of type `LoggingTool`
 - a `options` object of type `OptionsTool`
 - a `resources` object of type `ResourceManager`

'''
from reco3d.managers import ResourceManager
from reco3d.tools.logging import LoggingTool

class Process(object):
    req_opts = [] # list of required option keys
    default_opts = {} # names of each option with a default value associated with it

    opt_resources = {} # names of optional resources used by process { key : [resource_type_1, resource_type_2, ...], ... }
    req_resources = {} # names of resources required by process { key : [resource_type_1, resource_type_2, ...], ...}
                       # if list is empty, assume all resources are allowed (danger!)

    def __init__(self, options, **kwargs):
        self.options = options
        self.options.check_req(self.req_opts)
        self.options.set_default(self.default_opts)
        self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
        self.resources = ResourceManager(options.get('ResourceManager'))
        for key, value in kwargs.items():
            self.resources.add(value, key=key)
        self.logger.debug('{} initialized'.format(self))

    def config(self):
        for req_key, req_resource_types in self.req_resources.items():
            if not req_key in self.resources:
                err_msg = 'required resource {} missing'.format(req_key)
                self.logger.error(err_msg)
                raise RuntimeError(err_msg)
            elif req_resource_types is None:
                continue
            elif not type(self.resources[req_key]).__name__ in req_resource_types:
                err_msg = 'resource {} type is not in allowed resource types'.format(req_key)
                self.logger.error(err_msg)
                raise RuntimeError(err_msg)
        for opt_key, opt_resource_types in self.opt_resources.items():
            if opt_key in self.resources:
                if opt_resource_types is None:
                    continue
                elif not type(self.resources[opt_key]).__name__ in opt_resource_types:
                    err_msg = 'resource {} type is not in allowed resource types'.format(opt_key)
                    self.logger.error(err_msg)
                    raise RuntimeError(err_msg)

    def start(self):
        pass

    def run(self):
        pass

    def continue_run(self):
        return True

    def finish(self):
        pass

    def cleanup(self):
        pass
