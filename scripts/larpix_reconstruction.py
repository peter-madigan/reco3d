'''
A script for applying reconstructions to a larpix serial file (produced by dat2h5.py)

This script reads in hits from a raw larpix serial data file, applies a calibration, and then writes the data to the standard
larpix data file format
'''
import argparse
import os

from reco3d.managers import Manager
from reco3d.processes.larpix_processes import (LArPixDataReaderProcess, LArPixEventBuilderProcess, LArPixTrackReconstructionProcess, LArPixDataWriterProcess, LArPixDataCounterProcess, LArPixTriggerBuilderProcess)
from reco3d.resources.basic_resources import Resource
from reco3d.resources.larpix_resources import (LArPixSerialDataResource, LArPixDataResource)
from reco3d.tools.options import OptionsTool
from reco3d.tools.logging import LoggingTool

parser = argparse.ArgumentParser()
parser.add_argument('-i','--infile', type=str, required=True, help='path to input serial file')
parser.add_argument('-o','--outfile', type=str, default=None, help='path to output serial file')
parser.add_argument('-c','--config', type=str, default='larpix_reconstruction_conf.json',
                    help='path to options file (default: %(default)s')
parser.add_argument('-l','--logfile', type=str, default=None, help='path to log file (optional)')
parser.add_argument('-v','--verbose', action='store_true')
args = parser.parse_args()

# Get configuration options
infile = args.infile
outfile = args.outfile
configfile = args.config
if outfile is None:
    outfile = os.path.splitext(infile)[0] + '_reco.h5'
verbose = args.verbose
logfile = args.logfile

# Set configuration options
options = OptionsTool(filename=configfile)
if not logfile is None:
    options['LoggingTool']['outfile'][0] = True
    options['LoggingTool']['outfile'][2] = logfile
if verbose:
    options['LoggingTool']['stdout'][1] = 'debug'
    if not logfile is None:
        options_dict['LoggingTool']['outfile'][1] = 'debug'
options['LArPixSerialDataResource']['LArPixSerialConverter']['filename'] = infile
options['LArPixDataResource']['LArPixHDF5Converter']['filename'] = outfile

# Set up the manager and initialize the main logger
logger = LoggingTool(options.get('LoggingTool'))
manager = Manager(options.get('Manager'))

# Keep record of options
logger.info('Configuration - {}'.format(options))

# Create input file
infile_options = options.get('LArPixSerialDataResource')
infile_resource = LArPixSerialDataResource(infile_options)

# Create an active memory resource for the event builder (basically just a stack)
active_options = options.get('LArPixActiveResource')
active_resource = Resource(active_options)

# Create output file
outfile_options = options.get('LArPixDataResource')
outfile_resource = LArPixDataResource(outfile_options)

# Create a hit reader
reader_options = options.get('LArPixDataReaderProcess')
reader_process = LArPixDataReaderProcess(reader_options, in_resource=infile_resource, out_resource=active_resource)

# Create a trigger builder
triggerbuilder_options = options.get('LArPixTriggerBuilderProcess')
triggerbuilder_process = LArPixTriggerBuilderProcess(triggerbuilder_options, active_resource=active_resource)

# Create an event builder
eventbuilder_options = options.get('LArPixEventBuilderProcess')
eventbuilder_process = LArPixEventBuilderProcess(eventbuilder_options, active_resource=active_resource, out_resource=outfile_resource)

# Create an event counter
counter_options = options.get('LArPixDataCounterProcess')
counter_process = LArPixDataCounterProcess(counter_options, data_resource=active_resource)

# Create a track reconstruction
trackreco_options = options.get('LArPixTrackReconstructionProcess')
trackreco_process = LArPixTrackReconstructionProcess(trackreco_options, data_resource=outfile_resource)

# Create an event writer
writer_options = options.get('LArPixDataWriterProcess')
writer_process = LArPixDataWriterProcess(writer_options, in_resource=outfile_resource, out_resource=outfile_resource)

# Add processes to manager
manager.add_processes(reader_process, triggerbuilder_process, eventbuilder_process, trackreco_process, counter_process, writer_process)
# Add resources to manager
manager.add_resources(infile_resource, active_resource, outfile_resource)


# Run!
manager.config()

manager.start()
manager.run()
manager.finish()

manager.cleanup()
