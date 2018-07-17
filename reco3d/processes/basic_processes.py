from reco3d.managers import (Manager, ResourceManager)
from reco3d.tools.logging import LoggingTool

class Process(object):
    opt_resources = {} # names of optional resources used by process { key : [resource_type_1, resource_type_2, ...], ... }
    req_resources = {} # names of resources required by process { key : [resource_type_1, resource_type_2, ...], ...}
                       # if list is empty, assume all resources are allowed (danger!)

    def __init__(self, options, **kwargs):
        self.options = options
        self.logger = LoggingTool(options.get('LoggingTool'))
        self.resources = ResourceManager(options.get('ResourceManager'))
        for key, value in kwargs.items():
            self.resources.add(value, key=key)

    def config(self):
        for req_key, req_resource_types in self.req_resources.items():
            if not req_key in self.resources:
                raise RunTimeError('required resource {} missing'.format(req_key))
            elif not type(self.resources[req_key]).__name__ in req_resource_types:
                raise RunTimeError('resource {} type is not in allowed resource types'.format(req_key))

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
