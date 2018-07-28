'''
An example script demonstrating how a reco3d.Manager is initialized and run.

This script reads in hits from a raw larpix serial data file, applies a calibration, and then writes the data to the standard
larpix data file format
'''
import argparse

from reco3d.managers import Manager
from reco3d.processes.larpix_processes import (LArPixHitReaderProcess, LArPixCalibrationProcess, LArPixDataWriterProcess)
from reco3d.resources.larpix_resources import (LArPixSerialDataResource, LArPixDataResource, LArPixCalibrationDataResource)
from reco3d.tools.options import OptionsTool
from reco3d.tools.logging import LoggingTool

parser = argparse.ArgumentParser()
parser.add_argument('--options', type=str, default='example_conf.json', help='path to options configuration file (.json)')
args = parser.parse_args()

# Set up the manager and initialize the main logger and the "grandparent" options tool
options = OptionsTool(filename=args.options)
logger = LoggingTool(options.get('LoggingTool'))
manager = Manager(options.get('Manager'))

# Create a read-only serial file resource
serial_file_options = options.get('LArPixSerialDataResource')
serial_resource = LArPixSerialDataResource(serial_file_options) 

# Create a standard larpix data resource (for active-storage and writing)
file_options = options.get('LArPixDataResource')
file_resource = LArPixDataResource(file_options)

# Create a calibration data resource (for looking up calibration values)
calib_file_options = options.get('LArPixCalibrationDataResource')
calib_resource = LArPixCalibrationDataResource(calib_file_options)

# Create a hit reader to pull hits out of raw serial file
reader_options = options.get('LArPixHitReaderProcess')
reader_process = LArPixHitReaderProcess(reader_options, in_resource=serial_resource, out_resource=file_resource)

# Create a calibration process to pull data from the larpix data, apply a calibration, and place back into larpix data
calib_options = options.get('LArPixCalibrationProcess')
calib_process = LArPixCalibrationProcess(calib_options, data_resource=file_resource, calib_resource=calib_resource)

# Create a writing process that will pull active data and send to the larpix data write queue
writer_options = options.get('LArPixDataWriterProcess')
writer_process = LArPixDataWriterProcess(writer_options, in_resource=serial_resource, out_resource=file_resource)

# Add processes to manager 
manager.add_processes(reader_process, calib_process, writer_process) # order represents order of execution
# Add resources to manager
manager.add_resources(serial_resource, file_resource, calib_resource)


# Run!
manager.config()

manager.start()
manager.run()
manager.finish()

manager.cleanup()
