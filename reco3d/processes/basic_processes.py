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
            elif not type(self.resources[req_key]).__name__ in req_resource_types:
                err_msg = 'resource {} type is not in allowed resource types'.format(req_key)
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
