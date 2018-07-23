from reco3d.resources.basic_resources import Resource
from reco3d.converters.larpix_converters import LArPixHDF5Converter
import reco3d.tools.python as reco3d_pytools

class LArPixSerialDataResource(Resource):
    pass

class LArPixDataResource(Resource):
    '''
    This class handles queuing / storing / accessing data for the LArPix analysis files
    '''
    req_opts = Resource.req_opts + ['LArPixHDF5Converter']
    default_opts = reco3d_pytools.combine_dicts(\
        Resource.default_opts, { 'write_queue_length' : 100 # length of write queue before flushing to file
                                 })

    def config(self): # Resource method
        ''' Initialize converter and options '''
        super().config()

        self.converter = LArPixHDF5Converter(self.options.get('LArPixHDF5Converter'))
        self.write_queue_length = self.options['write_queue_length']

    def start(self): # Resource method
        ''' Open converter '''
        super().start()

        self.converter.open()

    def run(self): # Resource method
        ''' Clear stack and flush buffer '''
        super().run()

        for dtype in self._write_queue.keys():
            if len(self._write_queue[dtype]) > self.write_queue_length:
                self.flush_write_buffer(dtype)

    def finish(self): # Resource method
        ''' Flush all write buffers '''
        super().finish()

        for dtype in self._write_queue.keys():
            self.flush_write_buffer(dtype)

    def cleanup(self): # Resource method
        ''' Close converter '''
        super().cleanup()

        self.converter.close()

    def flush_write_buffer(self, dtype):
        ''' Flush write buffer of data type '''
        write_success = True
        for obj in self._write_queue[dtype]:
            write_success = self.converter.write(obj) and write_success
        if not write_success:
            self.logger.error('write failure - could not flush write buffer')
        else:
            self._write_queue[dtype] = []

class LArPixCalibrationDataResource(Resource):
    pass
