import reco3d.tools.python as reco3d_pytools
import reco3d.types as reco3d_types
from reco3d.processes.basic_processes import Process

class LArPixDataReaderProcess(Process):
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'dtypes' : ['Hit'], # list of data type names to try and read (None reads all types in resource)
                                'max' : 1 }) # how many objects to read (-1 reads all from resouce queue - not recommended)

    opt_resources = {}
    req_resources = {
        'in_resource': ['Resource','LArPixSerialDataResource','LArPixDataResource'],
        'out_resource': ['LArPixDataResource']
        }

    def config(self):
        ''' Apply options to process '''
        super().config()

        dtype_names = self.options['dtypes']
        if dtype_names is None:
            self.dtypes = None
        else:
            self.dtypes = []
            for dtype_name in dtype_names:
                self.dtypes += [getattr(reco3d_types, dtype_name)]

        self.max = self.options['max']

    def run(self):
        ''' Simply takes hits from the in_resource read_queue and moves them to the out_resource stack '''
        super().run()

        obj = None
        self.logger.debug(self.max)
        if self.dtypes is None:
            for dtype in self.resources['in_resource'].read_queue_dtypes():
                obj = self.resources['in_resource'].read(dtype, n=self.max)
        else:
            for dtype in self.dtypes:
                obj = self.resources['in_resource'].read(dtype, n=self.max)

        if obj is None:
            return
        self.resources['out_resource'].push(obj)

class LArPixCalibrationProcess(Process):
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'calibrations' : [], # list of calibrations to apply
                                'max' : 1 }) # max number of hits to pull from stack (-1 pulls all hits)

    opt_resources = {}
    req_resources = {
        'data_resource': ['Resource','LArPixSerialDataResource','LArPixDataResource'],
        'calib_resource': ['LArPixCalibrationDataResource']
        }

    def config(self):
        super().config()

        self.calibrations = self.options['calibrations']
        self.max = self.options['max']

    def run(self):
        '''
        Takes hits from the data_resource stack and applies the specified calibrations
        Puts hits back into stack after applying calibrations
        '''
        super().run()

        hits = self.resources['data_resource'].pop(reco3d_types.Hit, n=self.max)
        if hit is None:
            return

        calib_hits = self.do_calibrations(hits)

        self.resources['data_resource'].push(calib_hits)

    def do_calibrations(self, hits):
        ''' Apply calibrations given by options '''
        if not calibrations:
            return hits
        raise NotImplementedError

class LArPixDataWriterProcess(Process):
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'dtypes' : None, # which data types to write (None attempts to write all object types)
                                'max' : 1 }) # max number of data objects to write in each loop (None write all objects)

    opt_resouces = {}
    req_resources = {
        'in_resource': ['Resource','LArPixSerialDataResource','LArPixDataResource'],
        'out_resource': ['LArPixDataResource']
        }

    def config(self):
        ''' Apply options to process '''
        super().config()

        dtype_names = self.options['dtypes']
        if dtype_names is None:
            self.dtypes = None
        else:
            self.dtypes = []
            for dtype_name in dtype_names:
                self.dtypes += [getattr(reco3d_types, dtype_name)]

        self.max = self.options['max']

    def run(self):
        ''' Copies objects from the in_resource stack to the out_resource write_queue '''
        super().run()

        obj = None
        if self.dtypes is None:
            for dtype in self.resources['in_resource'].stack_dtypes():
                obj = self.resources['in_resource'].peek(dtype, n=self.max)
        else:
            for dtype in self.dtypes:
                obj = self.resources['in_resource'].peek(dtype, n=self.max)

        if obj is None:
            return
        self.resources['out_resource'].write(obj)

class LArPixEventBuilderProcess(Process):
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'max_nhit' : -1, # max number of hits in an event (-1 sets no limit)
                                'min_nhit' : 5, # min number of hits in an event
                                'dt_cut' : 10e3 }) # max dt between hits in an event [ns]
                                                   # (otherwise splits into two events)
    opt_resources = {}
    req_resources = {
        'data_resource': ['LArPixDataResource']
        }

    def config(self):
        ''' Apply options to process '''
        super().config()

        self.max_nhit = self.options['max_nhit']
        self.min_nhit = self.options['min_nhit']
        self.dt_cut = self.options['dt_cut']

    def run(self):
        '''
        Pull all hits from the stack, check if they form an isolated event(s)
        If so, assemble event from hits
        Then, push only next hits back to stack and also push event to stack

        Algorithm specifics:
         - Assumes that hits are in chronological order
         - An event is defined as a cluster of hits separated by no more than `dt_cut` ns
         between hits
         - An event is only chosen if there is a gap larger than `dt_cut` on both sides of the event
         - A hold is requested on the `Hit` stack, so that the subsequent iterations have access to
         previous hits

        '''
        super().config()

        hits = self.resources['data_resource'].pop(reco3d_types.Hit, n=self.max_nhit)
        events, remaining_hits = self.find_events(hits)
        if remaining_hits:
            self.resources['data_resource'].hold(reco3d_types.Hit)
        self.resources['data_resource'].push(remaining_hits)
        self.resources['data_resource'].push(events)

    def is_associated(self, hit, hits):
        ''' Apply selection criteria '''
        if hit is None:
            return False
        elif not hits:
            return True
        else:
            for other in hits:
                if abs(hit.ts - other.ts) < self.dt_cut:
                    return True
        return False

    def find_hit_clusters(self, hits):
        ''' Find isolated hit clusters '''
        hit_clusters = []
        curr_cluster = []
        for hit in hits:
            if self.is_associated(hit, curr_cluster) and (len(curr_cluster) < self.max_nhit
                                                          or self.max_nhit < 0):
                curr_cluster.append(hit)
            elif self.is_cluster(curr_cluster):
                hit_clusters += [curr_cluster]
                curr_cluster = [hit]
            else:
                curr_cluster = [hit]
        return hit_clusters, curr_cluster

    def find_events(self, hits):
        '''
        Find isolated hit clusters and convert them into event objects
        Note: event objects are created without event ids (this must be handled else where)
        '''
        clusters, remaining_hits = self.find_hit_clusters(hits)
        events = [reco3d_types.Event(evid=None, hits=cluster) for cluster in clusters]
        return events, remaining_hits
