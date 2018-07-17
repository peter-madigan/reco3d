# reco3d reconstruction software

## Basic guiding design principles
1. Build a lightweight reconstruction chain software based in python focussed on 3D hit
   reconstruction
2. Make reconstruction chain easily extendable to additional (unknown) data types and
   reconstruction methods

## Installation
 1. Clone this git repo.
 ```
 git clone <this repo>
 ```
 2. Install `reco3d`
 ```
 cd reco3d
 pip install .
 ```
 3. Check installation
 ```
 pytest
 ``` 

## Execution
The basic execution of a `reco3d` program involves a `reco3d.Manager`, along with an
assortment of `reco3d.processes` and `reco3d.resources`. Broadly speaking, their roles in the
program are:
 - `reco3d.Manager` keeps track of what is executing, when it should execute, and what "stage"
 of execution the program is in
 - `reco3d.processes` define fixed algorithms that are to be executed on data
 - `reco3d.resources` provide data to the `reco3d.processes`

Within a program, a single `reco3d.Manager` is created along with all necessary processes and
resources. A main `reco3d.tools.options.OptionsTool` object is created and handles process-
and resource-specific configuration. Processes are initialized with links to their required
resources or optional resources. The processes and resources are then added to the 
`reco3d.Manager`. This allows the manager to synchonize the execution of the program. The 
order in which processes are added to the manager specifies the order of execution. The 
`reco3d.Manager` then executes a series of stages:
 1. First the `config()` stage is executed. Each resource's `config()` method is executed,
 followed by each process's `config()` method. Resources are added to each process during this
 stage according to the specified requirements and options.
 2. The `start()` stage is executed next. Each resource's `start()` method is executed,
 followed by each process's `start()` method.
 3. The `run()` stage initiates an event loop in which each resource's then process's `run()`
 method is executed. At the end of each loop iteration, each process and each resource is
 asked whether the loop should continue via the `continue_run()` method. The loop continues as
 long as all of these calls return True. Any process or resource can signal an end to the 
 event loop via this method.
 4. The `finish()` stage is initiated after the event loop concludes. Each resource's
 `finish()` method is executed, followed by the process `finish()` methods
 5. Finally, the `cleanup()` stage is executed, signifying the end of the program. Each
 resource `cleanup()` method is run, followed by each process's.

## Structure
`reco3d` is built out of the following objects:
`reco3d.types`: classes used for passing data between reco3d objects
 - each has the following attributes:
   - consist of python `Number` objects or `Sequences` of other `reco3d.types` (insures fixed
   length for data storage)
   - __dict__ method provides access to all internal data
   - methods should only provide access to internal data, but not manipulate it (think of it
   as a C struct)

`reco3d.managers`: handles the execution and organization of the program
 - a single instance of a `Manager` is created in the execution script
 - communication between the `Manager` instance and the `reco3d.processes`/
 `reco3d.resources`/etc is accomplished through the `continue_run()` method
 - `ProcessManager` handles the order and execution of a collection of `reco3d.processes`
 - `ResourceManager` handles the access to and execution of a collection of `reco3d.resources

`reco3d.processes`: excutes a series of operations on `reco3d.types`
 - all internal data is fixed after the initialization / configuration stage
 - utilizes `reco3d.resources` and `reco3d.tools` to accomplish operations
 - a list of `req_resources` and `opt_resources` is specified by each process insure that the
 program will execute as expected
 - all process should accept as arguments an options argument of type `OptionsTool` and 
 utilize this interface to configure the process, additional keyword arguments should be used
 to specify resources used by the process

`reco3d.resources`: used by `reco3d.processes` to access / store data
 - makes use of a `reco3d.converter` to read and write data to an external source (like a data
 file)
 - typically contains a queue- and/or cache-like object(s) that can be accessed by
 `reco3d.processes`
   - queue: "live" data that `reco3d.processes` extract, remove, manipulate, and/or generate
     - typically a queue will refreshed at the end of the event loop
   - cache: a private data object that the `reco3d.resource` can use to speed up lookup times
     - cache data can be updated every event loop, but has a longer lifetime than queues
 - access to data is provided by the methods below
   - `read(dtype)`: grab next read object of data type `dtype` in read queue
   - `write(obj)`: put an object `obj` in the write queue
   - `get(loc, id)`: fetch object at `loc` that matches `id`
   - `set(loc, obj)`: replace object at `loc` with `obj`
   - `pop(dtype)`: grab next object in active stack, removing it from resource
   - `push(obj)`: insert object `obj` into the active stack
   - `clear(dtype)`: clear active data of data type `dtype`. If `dtype` in `None`, clear all.
   This method is typically called at every `run()` call
   - `hold(dtype)`: ask to hold active data of data type for another iteration

`reco3d.converters`: simple classes that give resources access to external data formats
 - translates external data formats into `reco3d.types`
 - `reco3d.resources` will exclusively use the `read()`, `write()`, `open()`, and `close()` methods
 - `converters` should be initialized using an `OptionsTool` object.

`reco3d.tools`: classes that handle specific functions unrelated to manipulating 
`reco3d.types` (e.g. logging, interpreting options, specialized algorithms, etc)

### Logging
Logging is handled through the built-in python library `logging`. To assist in setting up 
standard logging handlers, the `reco3d.tools.logging` module contains a `LoggingTool` class.
The `LoggingTool` acts as a wrapper class for the python `Logger` object. All `LoggingTool`
objects will provide `info()`, `warning()`, `error()`, `critical()`, and `debug()` methods.
Configuring `StreamHandlers`, `FileHandlers`, and `Formatters` along with log levels will be
performed through the `OptionsTool` argument passed into the `LoggingTool` at initialization.

### Map of included types with inheritance
As of July 2018:
```
reco3d --- types --- basic_types --- * Empty *
        |         |
        |         |- larpix_types --- Hit(object)
        |                          |- HitCollection(object)
        |                          |- Event(HitCollection)
        |
        |- managers --- Manager(object)
        |            |- ResourceManager(object)
        |            |- ProcessManager(object)
        |
        |- resources --- basic_resources --- Resource(object)
        |             |
        |             |- larpix_resources --- LArPixDataResource(Resource)
        |                                  |- LArPixSerialDataResource(Resource)
        |                                  |- LArPixCalibrationDataResource(Resource)
        |
        |- converters --- basic_converters --- Converter(object)
        |              |
        |              |- larpix_converters --- SerialConverter(Converter)
        |                                    |- HDF5Converter(Converter)
        |
        |- processes --- basic_processes --- Process(object)
        |             |
        |             |- larpix_processes --- LArPixFilter(Process)
        |                                  |- LArPixCalibrationProcess(Process)
        |                                  |- LArPixDataWriterProcess(Process)
        |
        |- tools --- logging --- LoggingTool(object)
                  |
                  |- options --- OptionsTool(object)
```
