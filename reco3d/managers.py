from reco3d.tools.logging import LoggingTool

class Manager(object):
      req_opts = [] # list of required options (raise error if not found)
      default_opts = {} # list of options arguments and default values

      def __init__(self, options):
            self.options = options
            self.options.check_req(self.req_opts)
            self.options.set_default(self.default_opts)
            self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
            self.resources = ResourceManager(options.get('ResourceManager'))
            self.processes = ProcessManager(options.get('ProcessManager'))
            self.logger.debug('{} initialized'.format(self))

      def add_resources(self, *args, **kwargs):
            for resource in args:
                  self.resources.add(resource)
            for key, resource in kwargs.items():
                  self.resources.add(resource, key=key)
            self.logger.debug('Resources added to Manager')

      def add_processes(self, *args):
            for process in args:
                  self.processes.add(process)
            self.logger.debug('Processes added to Manager')

      def config(self):
            self.resources.config()
            self.processes.config()
            self.logger.debug('config stage complete')

      def start(self):
            self.resources.start()
            self.processes.start()
            self.logger.debug('start stage complete')

      def run(self):
            while True:
                  self.resources.run()
                  self.processes.run()

                  if not self.resources.continue_run():
                        break
                  if not self.processes.continue_run():
                        break
            self.logger.debug('run stage complete')

      def finish(self):
            self.resources.finish()
            self.processes.finish()
            self.logger.debug('finish stage complete')
            
      def cleanup(self):
            self.resources.cleanup()
            self.processes.cleanup()
            self.logger.debug('cleanup stage complete')

class ResourceManager(object):
      req_opts = [] # list of required options (raise error if not found)
      default_opts = {} # list of options arguments and default values

      def __init__(self, options):
            self.options = options
            self.options.check_req(self.req_opts)
            self.options.set_default(self.default_opts)
            self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
            self._resources = {}
            self.logger.debug('{} initialized'.format(self))

      def __contains__(self, item):
            if isinstance(item, str):
                  # look for key
                  return item in self._resources.keys()
            # look for object
            return item in self._resources.values()

      def __getitem__(self, key):
            return self._resources[key]

      def __iter__(self):
            return iter(self._resources.values())

      def add(self, resource, key=None):
            resource_name = type(resource).__name__
            if not key is None:
                  resource_name = key
            if not resource_name in self._resources:
                  self._resources[resource_name] = resource
            else:
                  err_msg = 'resource already exists in ResourceManager'
                  self.error(err_msg)
                  raise ValueError(err_msg)

      def config(self):
            for resource in self:
                  resource.config()
            self.logger.debug('config complete')

      def start(self):
            for resource in self:
                  resource.start()
            self.logger.debug('start complete')

      def run(self):
            for resource in self:
                  resource.run()
            self.logger.debug('run complete')

      def continue_run(self):
            return all([resource.continue_run() for resource in self])

      def finish(self):
            for resource in self:
                  resource.finish()
            self.logger.debug('finish complete')

      def cleanup(self):
            for resource in self:
                  resource.cleanup()
            self.logger.debug('cleanup complete')

class ProcessManager(object):
      req_opts = [] # list of required options (raise error if not found)
      default_opts = {} # list of options arguments and default values

      def __init__(self, options):
            self.options = options
            self.options.check_req(self.req_opts)
            self.options.set_default(self.default_opts)
            self.logger = LoggingTool(options.get('LoggingTool'), name=self.__class__.__name__)
            self._processes = []
            self.logger.debug('{} initialized'.format(self))

      def __contains__(self, item):
            if isinstance(item, str):
                  # look for process of type
                  return item in [type(process).__name__ for process in self]
            # look for specific process
            return item in [process for process in self]

      def __iter__(self):
            return iter(self._processes)

      def add(self, process):
            self._processes += [process]

      def config(self):
            for process in self:
                  process.config()
            self.logger.debug('config complete')

      def start(self):
            for process in self:
                  process.start()
            self.logger.debug('start complete')

      def run(self):
            for process in self:
                  process.run()
            self.logger.debug('run complete')

      def continue_run(self):
            return all([process.continue_run() for process in self])

      def finish(self):
            for process in self:
                  process.finish()
            self.logger.debug('finish complete')

      def cleanup(self):
            for process in self:
                  process.cleanup()
            self.logger.debug('cleanup complete')
