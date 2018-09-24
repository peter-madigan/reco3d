'''
This module contains LArPix specific processes:
 - LArPixDataReaderProcess
 - LArPixCalibrationProcess
 - LArPixDataWriterProcess
 - LArPixEventBuilderProcess
'''
import numpy as np
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

class LArPixDataCounterProcess(Process):
    '''
    This process logs a message after a specified number of objects have gone through the stack or after a specified number of run executions
    '''
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'dtypes' : None, # which data types to update on (None updates all)
                                'interval' : 1000, # how often to update (default value)
                                'dtype_interval' : {}}) # how often to update specified data types

    opt_resources = {
        'data_resource': None
        }
    req_resources = {}

    def config(self):
        ''' Apply options to process '''
        super().config()

        self.dtypes = self.options['dtypes']
        self.interval = self.options['interval']
        self.dtype_name_interval = self.options['dtype_interval']

        self.counter = {}
        self.interval_counter = {}
        self.dtype_interval = {}

        if 'data_resource' in self.resources:
            for dtype_name in self.dtype_name_interval.keys():
                dtype = getattr(reco3d_types, dtype_name)
                self.counter[dtype] = 0
                self.interval_counter[dtype] = 0
                self.dtype_interval[dtype] = self.dtype_name_interval[dtype_name]
            if not self.dtypes is None:
                for dtype_name in self.dtypes:
                    dtype = getattr(reco3d_types, dtype_name)
                    if not dtype in self.counter.keys():
                        self.counter[dtype] = 0
                        self.interval_counter[dtype] = 0
                        self.dtype_interval[dtype] = self.interval
        self.counter['run iter'] = 0
        self.interval_counter['run iter'] = 0
        self.dtype_interval['run iter'] = self.interval

    def run(self):
        ''' Tallies executions and data types in stack, logs on specified interval '''
        super().run()

        self.counter['run iter'] += 1
        self.interval_counter['run iter'] += 1
        if 'data_resource' in self.resources:
            for dtype in self.resources['data_resource'].stack_dtypes():
                if dtype in self.counter:
                    self.counter[dtype] += len(self.resources['data_resource'].peek(dtype, n=-1))
                    self.interval_counter[dtype] += len(self.resources['data_resource'].peek(dtype, n=-1))
                elif self.dtypes is None:
                    try:
                        self.counter[dtype] += len(self.resources['data_resource'].peek(dtype, n=-1))
                        self.interval_counter[dtype] += len(self.resources['data_resource'].peek(dtype, n=-1))
                    except KeyError:
                        self.counter[dtype] = len(self.resources['data_resource'].peek(dtype, n=-1))
                        self.interval_counter[dtype] = len(self.resources['data_resource'].peek(dtype, n=-1))
                        self.dtype_interval[dtype] = self.interval
        for key in self.counter.keys():
            if self.interval_counter[key] >= self.dtype_interval[key]:
                self.logger.info('{} {}'.format(key, self.counter[key]))
                self.interval_counter[key] = 0

class LArPixDataWriterProcess(Process):
    '''
    This process grabs objects in the in resource stack and puts them in the out resource write queue
    options:
     - `dtypes`: list of data types to grab from stack and put into the write queue. None attempts to write all
     objects in stack
     - `max`: max number of objects to write on each event loop iteration (default: `-1`). If `-1`, writes all
     objects in resource queue

    resources:
     - `in_resource`: resource to grab from stack. Accepted types: all
     - `out_resource`: resource to write to. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
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

        if self.dtypes is None:
            for dtype in self.resources['in_resource'].stack_dtypes():
                obj = self.resources['in_resource'].peek(dtype, n=self.max)

                if obj is None:
                    continue
                self.resources['out_resource'].write(obj)
        else:
            for dtype in self.dtypes:
                obj = self.resources['in_resource'].peek(dtype, n=self.max)

                if obj is None:
                    continue
                self.resources['out_resource'].write(obj)

class LArPixTriggerBuilderProcess(Process):
    '''
    This process assembles Hits in the resource stack into ExternalTriggers. A trigger is
    defined by the channel mask and a coincidence interval. To register, the entire channel
    mask must be triggered within the coincidence interval.
    options:
    - `channel_mask`: list of (chipid, channel) pairs with external triggers enabled
    - `delay` : delay between real time trigger and channel trigger [ns]
    - `dt_cut`: time width of coincidence [ns]

    resources:
    - `active_resource`: resource to provide stack. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'channel_mask' : {}, # dict of (chip id : channel_list) pairs
                                                     # that are externally triggered
                                'delay' : 997e6, # delay between real time trigger and channel
                                                 # trigger [ns]
                                'dt_cut' : 1e3 }) # max dt between hits to be counted as
                                                  # external trigger
    opt_resources = {}
    req_resources = {
        'active_resource': None
        }

    def config(self): # Process method
        ''' Apply options to process '''
        super().config()

        self.channel_mask = dict([(int(chipid), channel_list)
                                  for chipid, channel_list in self.options['channel_mask'].items()])
        self.dt_cut = self.options['dt_cut']
        self.delay = self.options['delay']

    def run(self): # Process method
        '''
        Pull all hits from the stack, check if there are any isolated trigger events
        If so, convert to a single trigger and insert into stack.

        Algorithm specifics:
         - Assumes that hits are in chronological order
         - An trigger is defined as a cluster of hits separated by no more than `dt_cut` ns
         between hits and covering the entire channel mask
         - An trigger is only created if there is a gap larger than `dt_cut` on both sides of the trigger

        '''
        super().run()

        hits = reversed(self.resources['active_resource'].pop(reco3d_types.Hit, n=-1))
        triggers, skipped_hits, remaining_hits = self.find_triggers(hits)
        if remaining_hits:
            self.resources['active_resource'].preserve(reco3d_types.Hit)
        self.resources['active_resource'].push(skipped_hits)
        self.resources['active_resource'].push(remaining_hits)
        self.resources['active_resource'].push(triggers)

    def is_associated(self, hit, hits):
        ''' Apply hit selection criteria '''
        if hit is None:
            return False
        elif not hits:
            return True
        else:
            for other in hits:
                if abs(hit.ts - other.ts) < self.dt_cut:
                    return True
        return False

    def is_cluster(self, hits):
        ''' Apply event selection criteria '''
        hit_collection = reco3d_types.HitCollection(hits)
        triggered_channels = list(zip(hit_collection['chipid'], hit_collection['channelid']))
        if any([(chipid, channel) not in triggered_channels
                for chipid, channel_list in self.channel_mask.items()
                for channel in channel_list]):
            return False
        return True

    def find_hit_clusters(self, hits):
        ''' Find isolated hit clusters '''
        prev_hits = []
        hit_clusters = []
        curr_cluster = []
        for hit in hits:
            if self.is_associated(hit, curr_cluster):
                curr_cluster.append(hit)
            elif self.is_cluster(curr_cluster):
                hit_clusters += [curr_cluster]
                curr_cluster = [hit]
            else:
                prev_hits += curr_cluster
                curr_cluster = [hit]
        return prev_hits, hit_clusters, curr_cluster

    def find_triggers(self, hits):
        '''
        Find isolated hit clusters that match channel mask and convert them into trigger objects
        Note: trigger objects are created without trigger ids (this must be handled else where)
        '''
        skipped_hits, clusters, remaining_hits = self.find_hit_clusters(hits)
        triggers = []
        for cluster in clusters:
            hit_collection = reco3d_types.HitCollection(cluster)
            ts = min(hit_collection['ts'])
            triggers += [reco3d_types.ExternalTrigger(trig_id=None,
                                                      ts=hit_collection.ts_start,
                                                      delay=self.delay)]
        return triggers, skipped_hits, remaining_hits

class LArPixEventBuilderProcess(Process):
    '''
    This process assembles Hits in the active resource stack into Events. An Event is selected based on:
     - `nhit > min_nhit`
     - max separation between hits is no more than `dt_cut` ns
    options:
     - `max_nhit`: maximum number of hits in an event (-1 sets no upper limit)
     - `min_nhit`: minimum number of hits in an event
     - `dt_cut`: specifies Hit separation cut [ns]
     - `associate_triggers`: attempt to associate stack triggers to event. Not implemented!
     - `trigger_window`: 2 element list of `[min, max]` offset to trigger delay in ns. Triggers are
     associated if `event_start_timestamp` is within
     `[trig_timestamp - delay + min, trig_timestamp - delay + max]`

    resources:
     - `active_resource`: resource to provide stack. Accepted types: all
     - `out_resource`: resource to accept built events. Accepted types: all

    '''
    req_opts = Process.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(\
        Process.default_opts, { 'max_nhit' : -1, # max number of hits in an event (-1 sets no limit)
                                'min_nhit' : 5, # min number of hits in an event
                                'dt_cut' : 10e3, # max dt between hits in an event [ns]
                                                 # (otherwise splits into two events)
                                'associate_triggers' : True, # attempt to associate triggers in stack
                                                             # with events
                                'trigger_window' : [0, 300e3] # set trigger acceptance window [min, max]
                                                              # in ns
                                })
    opt_resources = {}
    req_resources = {
        'active_resource': None,
        'out_resource' : None
        }

    def config(self): # Process method
        ''' Apply options to process '''
        super().config()

        self.max_nhit = self.options['max_nhit']
        self.min_nhit = self.options['min_nhit']
        self.dt_cut = self.options['dt_cut']
        self.associate_triggers = self.options['associate_triggers']
        self.trigger_window = self.options['trigger_window']

    def run(self): # Process method
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
         - External triggers are assumed to come after associated events

        '''
        super().run()

        hits = self.resources['active_resource'].pop(reco3d_types.Hit, n=-1)
        if hits: hits = reversed(hits)
        events, skipped_hits, remaining_hits = self.find_events(hits)
        triggers = self.resources['active_resource'].peek(reco3d_types.ExternalTrigger, n=-1)
        if triggers: triggers = reversed(triggers)

        associated_events, unassociated_events = [], []
        if self.associate_triggers:
            associated_events, unassociated_events = self.find_associated_triggers(events, triggers)

        self.preserve_unfinished(remaining_hits, unassociated_events)
        self.resources['active_resource'].push(skipped_hits)
        self.resources['active_resource'].push(remaining_hits)
        self.resources['active_resource'].push(unassociated_events)

        if self.associate_triggers:
            self.resources['out_resource'].push(associated_events)
        else:
            self.resources['out_resource'].push(events)

    def preserve_unfinished(self, *args):
        ''' Preserve object types that are not 'null' '''
        for arg in args:
            if arg:
                if isinstance(arg, list):
                    self.resources['active_resource'].preserve(type(arg[0]))
                else:
                    self.resources['active_resource'].preserve(type(arg))

    def is_associated(self, hit, hits):
        ''' Apply hit selection criteria '''
        if hit is None:
            return False
        elif not hits:
            return True
        else:
            for other in hits:
                if abs(hit.ts - other.ts) < self.dt_cut:
                    return True
        return False

    def is_cluster(self, hits):
        ''' Apply event selection criteria '''
        if not len(hits) >= self.min_nhit:
            return False
        return True

    def find_hit_clusters(self, hits):
        ''' Find isolated hit clusters '''
        prev_hits = []
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
                prev_hits += curr_cluster
                curr_cluster = [hit]
        return prev_hits, hit_clusters, curr_cluster

    def find_events(self, hits):
        '''
        Find isolated hit clusters and convert them into event objects
        Note: event objects are created without event ids (this must be handled else where)
        '''
        skipped_hits, clusters, remaining_hits = self.find_hit_clusters(hits)
        events = [reco3d_types.Event(evid=None, hits=cluster) for cluster in clusters]
        return events, skipped_hits, remaining_hits

    def in_trigger_window(self, event, trigger):
        '''
        Return true if any part of event is within the specifed trigger window
        Trigger window is defined as `[trigger.ts - trigger.delay + trigger_window[0],
        trigger.ts - trigger.delay + trigger_window[1]]`
        '''
        if event.ts_end < trigger.ts - trigger.delay + self.trigger_window[0]:
            return False
        elif event.ts_start > trigger.ts - trigger.delay + self.trigger_window[1]:
            return False
        return True

    def find_associated_triggers(self, events, triggers):
        '''
        Find and associate triggers with events
        '''
        associated_events = []
        unassociated_events = []
        if not triggers or not events:
            return [], events
        for event in events:
            associated_triggers = []
            for trigger in triggers:
                if self.in_trigger_window(event, trigger):
                    associated_triggers += [trigger]
            if associated_triggers:
                new_event = event
                new_event.triggers += associated_triggers
                associated_events += [new_event]
            else:
                unassociated_events += [event]

        return associated_events, unassociated_events

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
        points = np.array(list(zip(x,y,z)))
        params = hough.HoughParameters()
        params.ndirections = self.hough_ndir
        params.npositions = self.hough_npos
        lines, points, params = hough.run_iterative_hough(points,
                params, self.hough_threshold, self.hough_cache)

        tracks = []
        for line, hit_idcs in lines.items():
            hits = event[list(hit_idcs)]
            tracks += [reco3d_types.Track(hits=hits, theta=line.theta, phi=line.phi,
                xp=line.xp, yp=line.yp, cov=line.cov)]
        return tracks
