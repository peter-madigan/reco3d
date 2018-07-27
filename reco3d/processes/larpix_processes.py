'''
This module contains LArPix specific processes:
 - LArPixDataReaderProcess
 - LArPixCalibrationProcess
 - LArPixDataWriterProcess
 - LArPixEventBuilderProcess
'''
import reco3d.tools.algorithms.hough as hough
import reco3d.tools.python as reco3d_pytools
import reco3d.types as reco3d_types
from reco3d.processes.basic_processes import Process

class LArPixDataReaderProcess(Process):
    '''
    This process reads a specified number of objects from the `in_resource` and places them in
    the `out_resource` stack
    options:
     - `dtypes`: list of objects to try to read from in resource (default: `Hit`). If `None`, reads
     all data types in resource
     - `max`: max number of objects to read from resource on each event loop iteration (default: `1`).
     If `-1`, reads all objects in resource queue

    resources:
     - `in_resource`: resource to read from. Accepted types: all
     - `out_resource`: resource to fill stack. Accepted types: all
    '''
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'dtypes' : ['Hit'], # list of data type names to try and read (None reads all types in resource)
                                'max' : 1 }) # how many objects to read (-1 reads all from resouce queue - not recommended)

    opt_resources = {}
    req_resources = {
        'in_resource': None,
        'out_resource': None,
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
    '''
    This process grabs a specified number of Hits from the data resource stack and applies a variety
    of calibrations to the Hit. It then places them back into the data resource stack
    options:
     - `calibration`: list of calibrations to apply to hit (default: []). Currently no calibrations
     are implemented
     - `max`: max number of Hits to read from resource on each event loop iteration (default: `1`).
     If `-1`, reads all objects in resource queue

    resources:
     - `calib_resource`: resource to read calibration data from. Accepted types: `LArPixCalibrationDataResource` only
     - `data_resource`: resource to provide stack. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'calibrations' : [], # list of calibrations to apply
                                'max' : 1 }) # max number of hits to pull from stack (-1 pulls all hits)

    opt_resources = {}
    req_resources = {
        'data_resource': None,
        'calib_resource': ['LArPixCalibrationDataResource']
        }

    def config(self):
        ''' Apply options to process '''
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
    '''
    This process grabs objects in the in resource stack and puts them in the out resource write queue
    options:
     - `dtypes`: list of data types to grab from stack and put into the write queue. None attempts to write all
     objects in stack
     - `max`: max number of objects to write on each event loop iteration (default: `-1`). If `-1`, writes all
     objects in resource queue

    resources:
     - `in_resource`: resource to grad from stack. Accepted types: all
     - `out_resource`: resource to write to. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'dtypes' : None, # which data types to write (None attempts to write all object types)
                                'max' : -1 }) # max number of data objects to write in each loop (-1 write all objects)

    opt_resouces = {}
    req_resources = {
        'in_resource': None,
        'out_resource': None
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
    '''
    This process assembles Hits in the in resource stack into Events. An Event is selected based on:
     - `nhit > min_nhit`
     - max separation between hits is no more than `dt_cut` ns
    options:
     - `max_nhit`: maximum number of hits in an event (-1 sets no upper limit)
     - `min_nhit`: minimum number of hits in an event
     - `dt_cut`: specifies Hit separation cut in ns

    resources:
     - `data_resource`: resource to provide stack. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'max_nhit' : -1, # max number of hits in an event (-1 sets no limit)
                                'min_nhit' : 5, # min number of hits in an event
                                'dt_cut' : 10e3 }) # max dt between hits in an event [ns]
                                                   # (otherwise splits into two events)
    opt_resources = {}
    req_resources = {
        'data_resource': None
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

        hits = self.resources['data_resource'].pop(reco3d_types.Hit, n=-1)
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

class LArPixTrackReconstructionProcess(Process):
    '''
    This process extracts tracks from Events in the data resource stack using a Hough
    transformation and a PCA analysis
    options:
     - `hough_threshold`: minimum number of hits in a track (default: 5)
     - `hough_ndir`: number of directions for Hough transform to generate (default: 1000)
     - `hough_npos`:

    resources:
     - `data_resource`: resource to provide stack. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_ops = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'hough_threshold' : 5,
                                'hough_ndir' : 1000,
                                'hough_npos' : 30 })
    opt_resources = {}
    req_resources = {
        'data_resource': None
        }

    def config(self):
        ''' Apply options to process '''
        super().config()

        self.hough_threshold = self.options['hough_threshold']
        self.hough_ndir = self.options['hough_ndir']
        self.hough_npos = self.options['hough_npos']
        self.hough_cache = hough.setup_fit_errors()

    def run(self):
        '''
        Pull all events from stack. For each event, perform the track reconstruction
        algorithm. Put events back into the stack with associated tracks.

        '''
        super().config()

        events = self.resources['data_resource'].pop(reco3d_types.Event, n=-1)
        if events is None:
            return
        for event in events:
            tracks = self.extract_tracks(event)
            event.reco_objs += tracks
        self.resources['data_resource'].push(events)

    def extract_tracks(self, event):
        ''' Perform hough transform algorithm and return found tracks '''
        x = np.array(event['px'])/10
        y = np.array(event['py'])/10
        z = np.array(event['ts'] - event.ts_start)/1000
        # FIXME: assumes t0 is at event start
        points = np.arry(list(zip(x,y,z)))
        params = hough.HoughParameters()
        params.ndirections = self.hough_ndir
        params.npositions = self.hough_npos
        lines, points, params = hough.run_iterative_hough(points,
                params, self.hough_threshold, self.hough_cache)

        tracks = []
        for line, hit_idcs in lines.items():
            hits = event[list(hit_idcs)]
            tracks += [Track(hits=hits, theta=line.theta, phi=line.phi,
                xp=line.xp, yp=line.yp, cov=line.cov)]
        return tracks
