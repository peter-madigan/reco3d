from reco3d.tools.logging import LoggingTool

class Manager(object):
      def __init__(self, options):
            self.options = options
            self.logger = LoggingTool(options.get(LoggingTool.__name__))
            self.resources = ResourceManager(options.get(ResourceManager.__name__))
            self.processes = ProcessManager(options.get(ProcessManager.__name__))

      def add_resources(self, *args, **kwargs):
            for resource in args:
                  self.resources.add(resource)
            for key, resource in kwargs.items():
                  self.resources.add(resource, key=key)

      def add_processes(self, *args):
            for process in args:
                  self.processes.add(process)

      def config(self):
            self.resources.config()
            self.processes.config()

      def start(self):
            self.resources.start()
            self.processes.start()

      def run(self):
            while True:
                  self.resources.run()
                  self.processes.run()

                  if not self.resources.continue_run(): break
                  if not self.processes.continue_run(): break

      def finish(self):
            self.resources.finish()
            self.processes.finish()
            
      def cleanup(self):
            self.resources.cleanup()
            self.processes.cleanup()

class ResourceManager(object):
      def __init__(self, options):
            self.options = options
            self.logger = LoggingTool(options.get(LoggingTool.__name__))
            self._resources = {}

      def __contains__(self, item):
            if isinstance(item, str):
                  # look for key
                  return item in self._resources.keys()
            else:
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
                  raise ValueError('resource already exists in ResourceManager')

      def config(self):
            for resource in self: resource.config()

      def start(self):
            for resource in self: resource.start()

      def run(self):
            for resource in self: resource.run()

      def continue_run(self):
            return all([resource.continue_run() for resource in self])

      def finish(self):
            for resource in self: resource.finish()

      def cleanup(self):
            for resource in self: resource.cleanup()

class ProcessManager(object):
      def __init__(self, options):
            self.options = options
            self.logger = LoggingTool(options.get(LoggingTool.__name__))
            self._processes = []

      def __contains__(self, item):
            if isinstance(item, str):
                  # look for process of type
                  return item in [type(process).__name__ for process in self]
            else:
                  # look for specific process
                  return item in [process for process in self]

      def __iter__(self):
            return iter(self._processes)

      def add(self, process):
            self._processes += [process]

      def config(self):
            for process in self: process.config()

      def start(self):
            for process in self: process.start()

      def run(self):
            for process in self: process.run()

      def continue_run(self):
            return all([process.continue_run() for process in self])

      def finish(self):
            for process in self: process.finish()

      def cleanup(self):
            for process in self: process.cleanup()
