'''
This module contains converters used by LArPix reconstruction and analysis.
The module requirements are `h5py` and `numpy`.

LArPixHDF5Converter handles reading and writing to "larpix analysis files" which contain event,
track, and hit data.

LArPixSerialConverter handles reading from "larpix serial files" produces by the dat2h5.py script.

'''
from reco3d.converters.basic_converters import Converter
import reco3d.tools.python as reco3d_pytools
import reco3d.types as reco3d_types
import h5py
import numpy as np

region_ref = h5py.special_dtype(ref=h5py.RegionReference)

class LArPixSerialConverter(Converter):
    '''
    A Converter-type class for reading from ROOT and HDF5 files produced by the dat2h5.py script
    Currently only reading Hit objects from HDF5 files is supported
    options:
     - `"filename"` : path to serial file to be read from

    Locating objects: hits are indexed according to their position in the serial data stream to look
    up a specific hit use `loc=<row index>`

    '''
    req_opts = Converter.req_opts + ['filename']
    default_opts = reco3d_pytools.combine_dicts(Converter.default_opts, {})

    _name_lookup = { # col: name of hdf5 serial file
        0 : 'channelid',
        1 : 'chipid',
        2 : 'pixelid',
        3 : 'pixelx',
        4 : 'pixely',
        5 : 'raw_adc',
        6 : 'raw_timestamp',
        7 : 'adc',
        8 : 'timestamp',
        9 : 'serialblock',
        10 : 'v',
        11 : 'pdst_v'
        }
    _col_lookup = dict([(name, col) for col, name in _name_lookup.items()])

    def __init__(self, options):
        super().__init__(options)
        self.filename = self.options['filename']
        self.is_open = False
        self.datafile = None
        self.read_idx = 0

        self.logger.debug('{} initialized'.format(self))

    def open(self): # Converter method
        ''' Open converter (typically occurs during config phase) '''
        if not self.is_open:
            # open file
            self.datafile = h5py.File(self.filename)
        self.is_open = True
        self.logger.debug('{} opened'.format(self))

    def close(self): # Converter method
        ''' Close converter (typically occurs during cleanup phase) '''
        if self.is_open:
            self.datafile.close()
        self.is_open = False
        self.logger.debug('{} closed'.format(self))

    def read(self, dtype, loc=None): # Converter method
        '''
        Looking at `loc`, return objects that match type
        If `loc` is `None`, return "next" `Hit`
        If `dtype` is other than `Hit`, logs error and returns `None`
        '''
        if not dtype == reco3d_types.Hit:
            self.logger.error('LArPixSerialConverter does not support reading non-Hit types')
            return None
        if not self.is_open:
            self.open()
        read_idx = loc
        if read_idx is None:
            read_idx = self.read_idx
            self.read_idx += 1
        if read_idx >= self.datafile['data'].shape[0]:
            return None
        hit = self.convert_row_to_hit(read_idx)
        return hit

    def write(self, obj): # Converter method
        '''
        LArPixSerialConverter is a read-only Converter
        This will log and error and return False
        '''
        self.logger.error('LArPixSerialConverter is read-only')
        return False

    def convert_row_to_hit(self, row_idx):
        ''' Looks up data at row_idx and returns a corresponding `Hit` object '''
        row_data = self.datafile['data'][row_idx]
        row_dict = dict([(name, row_data[col]) for name, col in self._col_lookup.items()])
        hit = reco3d_types.Hit(hid=row_idx, px=row_dict['pixelx'], py=row_dict['pixely'],
                               ts=row_dict['timestamp'], q=(row_dict['v'] - row_dict['pdst_v']),
                               chipid=row_dict['chipid'], channelid=row_dict['channelid'])
        return hit

class LArPixHDF5Converter(Converter):
    '''
    A Converter-type class for handling two-way communication with an HDF5 file used for reconstruction
    options:
        - `"filename"`: path to file

    Locating objects: HDF5 file structure is organized at the top level by object type. Each object type has its own
    dataset with the naming scheme described by `LArPixHDF5Converter.type_lookup`. Each dataset consists of rows of
    numpy arrays described by `dataset_desc`. To lookup/store an object at a specific row index, use `loc=<row idx>`.

    '''
    req_opts = Converter.req_opts + ['filename'] # list of required options (raises error if not found)
    default_opts = reco3d_pytools.combine_dicts(Converter.default_opts, {}) # list of option arguments with default values

    type_lookup = {
        reco3d_types.Hit : 'hits',
        reco3d_types.Event : 'events',
        reco3d_types.Track : 'tracks'
        reco3d_types.ExternalTrigger : 'triggers'
        }
    rev_type_lookup = dict([(item, key) for key, item in type_lookup.items()])

    dataset_desc = {
        'info' : None,
        'hits' : [
            ('hid', 'i8'),
            ('px', 'i8'), ('py', 'i8'), ('ts', 'i8'), ('q', 'i8'),
            ('iochain', 'i8'), ('chipid', 'i8'), ('channelid', 'i8'),
            ('geom', 'i8'), ('event_ref', region_ref), ('track_ref', region_ref)],
        'events' : [
            ('evid', 'i8'), ('track_ref', region_ref), ('hit_ref', region_ref),
            ('nhit', 'i8'), ('q', 'i8'), ('ts_start', 'i8'), ('ts_end', 'i8'),
            ('trigger_ref', region_ref)],
        'tracks' : [
            ('track_id','i8'), ('event_ref', region_ref), ('hit_ref', region_ref),
            ('theta', 'f8'),
            ('phi', 'f8'), ('xp', 'f8'), ('yp', 'f8'), ('nhit', 'i8'),
            ('q', 'i8'), ('ts_start', 'i8'), ('ts_end', 'i8'),
            ('sigma_theta', 'f8'), ('sigma_phi', 'f8'), ('sigma_x', 'f8'),
            ('sigma_y', 'f8')],
        'triggers' : [
            ('trig_id', 'i8'), ('event_ref', region_ref), ('trig_id', 'i8'),
            ('ts', 'i8'), ('delay', 'i8'), ('trig_type', 'i8')]
        }

    def __init__(self, options):
        super().__init__(options)
        self.filename = self.options['filename']
        self.is_open = False
        self.datafile = None
        self.read_idx = dict([(dset_name, 0) for dset_name in self.rev_type_lookup])
        self.write_idx = dict([(dset_name, 0) for dset_name in self.rev_type_lookup])

        self.logger.debug('{} initialized'.format(self))

    def open(self): # Converter method
        '''
        Open converter (typically occurs during config phase)
        '''
        if not self.is_open:
            # open file
            self.datafile = h5py.File(self.filename)
            # update write indices to end of arrays
            for dataset_name in self.datafile.keys():
                if dataset_name in self.rev_type_lookup.keys():
                    self.write_idx[dataset_name] = self.datafile[dataset_name].shape[0]
        # create any missing datasets
        for dataset_name in self.rev_type_lookup.keys():
            if not dataset_name in self.datafile.keys():
                self.create_dataset(dataset_name)
        self.is_open = True
        self.logger.debug('{} opened'.format(self))

    def close(self): # Converter method
        '''
        Close converter (typically occurs during cleanup phase)
        '''
        if self.is_open:
            self.datafile.close()
        self.is_open = False
        self.logger.debug('{} closed'.format(self))

    def read(self, dtype, loc=None): # Converter method
        '''
        Looking at loc, return objects that match type
        If loc is None, return "next" object
        '''
        if not dtype in self.type_lookup:
            return None
        if not self.is_open:
            self.open()
        dset_name = self.type_lookup[dtype]

        if dset_name == 'hits':
            hit = self.read_hit(loc)
            return hit

        elif dset_name == 'tracks':
            track = self.read_track(loc)
            return track

        elif dset_name == 'events':
            event = self.read_event(loc)
            return event

        elif dset_name == 'triggers':
            trigger = self.read_trigger(loc)
            return trigger

        return None

    def write(self, data, loc=None): # Converter method
        '''
        Write data to location. If None specified, append to end of dataset
        return True if successful, False if not
        '''
        if not isinstance(data, tuple(self.type_lookup.keys())):
            return False
        if not self.is_open:
            self.open()
        dset_name = self.type_lookup[type(data)]

        if dset_name == 'hits':
            self.write_hit(data, loc)
            return True

        elif dset_name == 'tracks':
            self.write_track(data, loc)
            return True

        elif dset_name == 'events':
            self.write_event(data, loc)
            return True

        elif dset_name == 'trigger':
            self.write_trigger(data, loc)
            return True

        return False

    def create_dataset(self, name):
        '''
        Initialize a dataset with name
        '''
        if not name in self.datafile.keys():
            self.datafile.create_dataset(name, (0,), maxshape=(None,),
                                         dtype=self.dataset_desc[name])

# Methods for generating data from reco3d types
    def reco3d_type_to_hdf5(self, reco3d_type_obj, **kwargs):
        '''
        Automatically generate numpy array used by hdf5
        Generates a numpy structured array with the dtype described by
        dataset_desc for the object type. Any fields that are None or nonexistant
        in the object stored with a default value of -9999, except for region references
        which are left uninitialized. Any fields that are in the dataset description, but
        are not explicit in vars(reco3d_type_obj) should be set manually using keyword
        arguments.
        '''
        if not isinstance(reco3d_type_obj, tuple(self.type_lookup.keys())):
            return None
        data_dict = vars(reco3d_type_obj).copy()
        dataset_name = self.type_lookup[type(reco3d_type_obj)]
        for value_name, value in kwargs.items():
            data_dict[value_name] = value
        # special actions for different data types
        self.fill_empty_dict(data_dict, dataset_name)
        data_tuple = tuple(data_dict[entry_desc[0]] for entry_desc in \
                               self.dataset_desc[dataset_name])
        return np.array(data_tuple, dtype=self.dataset_desc[dataset_name])

    @classmethod
    def fill_empty_dict(cls, data_dict, dataset_name):
        ''' Fill with empty values (if necessary) '''
        for entry_desc in cls.dataset_desc[dataset_name]:
            key = entry_desc[0]
            if not key in data_dict:
                if entry_desc[1] == region_ref:
                    data_dict[key] = None
                else:
                    data_dict[key] = -9999
            elif data_dict[key] is None and not entry_desc[1] == region_ref:
                data_dict[key] = -9999

    def hit_to_hdf5(self, hit, idx=None, event_ref=None, track_ref=None, **kwargs):
        '''
        Returns array representing a hit that can be saved in the hdf5 format
        References must be passed in as arguments
        '''
        data = self.reco3d_type_to_hdf5(hit, idx=idx, event_ref=event_ref, track_ref=track_ref, **kwargs)
        return data

    def track_to_hdf5(self, track, idx=None, hit_ref=None, event_ref=None, **kwargs):
        '''
        Returns array representing a track that can be saved in the hdf5 format
        References must be passed in as arguments
        '''
        new_kwargs = {}
        if track.cov is not None:
            s_theta, s_phi, s_x, s_y = np.sqrt(np.diag(track.cov))
            new_kwargs['sigma_theta'] = s_theta
            new_kwargs['sigma_phi'] = s_phi
            new_kwargs['sigma_x'] = s_x
            new_kwargs['sigma_y'] = s_y
        data = self.reco3d_type_to_hdf5(track, idx=idx, hit_ref=hit_ref, track_ref=event_ref,
                                        **new_kwargs, **kwargs)
        return data

    def event_to_hdf5(self, event, idx=None, hit_ref=None, track_ref=None, trigger_ref=None,
                      **kwargs):
        '''
        Returns array representing an event that can be saved in the hdf5 format
        References must be passed in as arguments
        '''
        data = self.reco3d_type_to_hdf5(event, idx=idx, hit_ref=hit_ref, track_ref=track_ref,
                                        trigger_ref=trigger_ref, **kwargs)
        return data

    def trigger_to_hdf5(self, trigger, idx=None, event_ref=None, **kwargs):
        '''
        Returns array representing a trigger that can be saved in the hdf5 format
        References must be passed in as arguments
        '''
        data = self.reco3d_typ_to_hdf5(trigger, idx=idx, event_ref=event_ref, **kwargs)

# Methods for converting data to a reco3d type
    def hdf5_to_reco3d_type(self, dtype, data, replace_defaults=True, **kwargs):
        '''
        Convert a numpy array into a reco3d type
        Any arguments that should be passed into the reco3d type that are not in the
        array names, should be passed as keyword arguments
        If replace_defaults is True, values with -9999 will be automatically replaced
        with None
        '''
        if not dtype in self.type_lookup.keys():
            return None
        dset_name = self.type_lookup[dtype]
        args_dict = {}
        for key in data.dtype.names:
            args_dict[key] = data[key]
        for key, value in kwargs.items():
            args_dict[key] = value
        if replace_defaults:
            self.replace_default_with_none(args_dict)
        obj = (dtype)(**args_dict)
        return obj

    @classmethod
    def replace_default_with_none(cls, args_dict):
        '''
        Fill all instances of -9999 with None
        '''
        for key, value in args_dict.items():
            if isinstance(value, (list, np.ndarray)):
                continue
            elif value == -9999:
                args_dict[key] = None

    def hdf5_to_hit(self, data, replace_defaults=True, **kwargs):
        ''' Returns a hit object represented by the data '''
        hit = self.hdf5_to_reco3d_type(reco3d_types.Hit, data, replace_defaults=replace_defaults, **kwargs)
        return hit

    def hdf5_to_track(self, data, replace_defaults=True, **kwargs):
        ''' Returns a track object represented by the data '''
        new_kwargs = {}
        hits = []
        for hit_data in self.datafile[data['hit_ref']][data['hit_ref']]:
            hits += [self.hdf5_to_hit(hit_data, replace_defaults=replace_defaults)]
        new_kwargs['hits'] = hits
        if any([data[key] == -9999 for key in ['sigma_theta', 'sigma_phi', 'sigma_x']]):
            new_kwargs['cov'] = None
        else:
            new_kwargs['cov'] = np.diag(np.array([data['sigma_theta'], data['sigma_phi'], data['sigma_x'],
                                                  data['sigma_y']]))
        track = self.hdf5_to_reco3d_type(reco3d_types.Track, data, replace_defaults=replace_defaults,
                                         **new_kwargs, **kwargs)
        return track

    def hdf5_to_event(self, data, replace_defaults=True, **kwargs):
        ''' Returns an event object represented by the data '''
        new_kwargs = {}
        hits = []
        for hit_data in self.datafile[data['hit_ref']][data['hit_ref']]:
            hits += [self.hdf5_to_hit(hit_data, replace_defaults=replace_defaults)]
        new_kwargs['hits'] = hits
        triggers = []
        for trigger_data in self.datafile[data['trigger_ref']][data['trigger_ref']]:
            triggers += [self.hdf5_to_trigger(trigger_data, replace_defaults=replace_defaults)]
        new_kwargs['triggers'] = triggers
        new_kwargs['reco_objs'] = []
        for track_data in self.datafile[data['track_ref']][data['track_ref']]:
            new_kwargs['reco_objs'] += [self.hdf5_to_track(track_data, replace_defaults=replace_defaults)]
        event = self.hdf5_to_reco3d_type(reco3d_types.Event, data, replace_defaults=replace_defaults,
                                         **new_kwargs, **kwargs)
        return event

    def hdf5_to_trigger(self, data, replace_defaults=True, **kwargs):
        ''' Returns an ExternalTrigger object represented by the data '''
        trigger = self.hdf5_to_reco3d_type(reco3d_types.ExternalTrigger, data,
                                        replace_defaults=replace_defaults, **kwargs)
        return trigger

# Methods for reading specific data types
    def read_hit(self, loc):
        '''
        Return hit at index specified by loc.
        If loc is None, return hit at current index and increment index
        '''
        dset_name = self.type_lookup[reco3d_types.Hit]
        read_idx = loc
        if read_idx is None:
            read_idx = self.read_idx[dset_name]
            self.read_idx[dset_name] += 1

        data = self.datafile[dset_name][read_idx]
        hit = self.hdf5_to_hit(data)
        return hit

    def read_track(self, loc):
        '''
        Return track at index specified by loc.
        If loc is None, return track at current index and increment index
        '''
        dset_name = self.type_lookup[reco3d_types.Track]
        read_idx = loc
        if read_idx is None:
            read_idx = self.read_idx[dset_name]
            self.read_idx[dset_name] += 1

        data = self.datafile[dset_name][read_idx]
        track = self.hdf5_to_track(data)
        return track

    def read_event(self, loc):
        '''
        Return event at index specified by loc
        If loc is None, return event at current index and increment index
        '''
        dset_name = self.type_lookup[reco3d_types.Event]
        read_idx = loc
        if read_idx is None:
            read_idx = self.read_idx[dset_name]
            self.read_idx[dset_name] += 1

        data = self.datafile[dset_name][read_idx]
        event = self.hdf5_to_event(data)
        return event

    def read_trigger(self, loc):
        '''
        Return a trigger at the index specified by loc
        If loc is None, return trigger at current index and increment index
        '''
        dset_name = self.type_lookup[reco3d_types.ExternalTrigger]
        read_idx = loc
        if read_idx is None:
            read_idx = self.read_idx[dset_name]
            self.read_idx[dset_name] += 1

        data = self.datafile[dset_name][read_idx]
        trigger = self.hdf5_to_trigger(data)
        return trigger

# Methods for writing data
    def write_data(self, dset_name, write_data, loc=None):
        '''
        Write an object to a particular dataset and location
        If loc is larger than current array size, resize array accordingly
        Returns row index of object written
        '''
        write_idx = loc
        if write_idx is None:
            write_idx = self.write_idx[dset_name]
            self.write_idx[dset_name] += 1
        if self.datafile[dset_name].shape[0] <= write_idx:
            self.datafile[dset_name].resize(write_idx + 1, axis=0)

        self.datafile[dset_name][write_idx] = write_data
        return write_idx

    def write_hit(self, hit, loc, event_idcs=None, track_idcs=None, **kwargs):
        ''' Write a hit to row index specified by `loc`, returns index of written hit '''
        hit_dset_name = self.type_lookup[type(hit)]
        event_ref = None
        if event_idcs:
            event_ref = self.datafile['events'].regionref[event_idcs]
        track_ref = None
        if track_idcs:
            track_ref = self.datafile['tracks'].regionref[track_idcs]
        hit_data = self.reco3d_type_to_hdf5(hit, event_ref=event_ref, track_ref=track_ref, **kwargs)
        return self.write_data(hit_dset_name, hit_data, loc)

    def write_track(self, track, loc, event_idcs=None, hit_idcs=None, **kwargs):
        ''' Write a track at row index specified by `loc` '''
        # write track in correct location with uninitialized references
        event_dset_name = self.type_lookup[reco3d_types.Event]
        event_ref = None
        if event_idcs:
            event_ref = self.datafile[event_dset_name].regionref[event_idcs]
        hit_dset_name = self.type_lookup[reco3d_types.Hit]
        hit_ref = None
        if hit_idcs:
            hit_ref = self.datafile[hit_dset_name].regionref[hit_idcs]
        track_dset_name = self.type_lookup[reco3d_types.Track]
        track_data = self.reco3d_type_to_hdf5(track, event_ref=event_ref, hit_ref=hit_ref, **kwargs)
        track_idx = self.write_data(track_dset_name, track_data, loc)

        if not hit_idcs is None:
            return track_idx

        # store hits if no hit_idcs are given
        track_idcs = [track_idx]
        if hit_idcs is None and track.hits:
            # store hits
            hit_idcs = []
            for hit in track.hits:
                hit_idcs += [self.write_hit(hit, None, event_idcs=event_idcs, track_idcs=track_idcs)]
            # re-store track with reference to hits
            hit_ref = self.datafile[hit_dset_name].regionref[sorted(hit_idcs)]
            track_data = self.reco3d_type_to_hdf5(track, event_ref=event_ref, hit_ref=hit_ref, **kwargs)
            track_idx = self.write_data(track_dset_name, track_data, track_idx)

        return track_idx

    def write_event(self, event, loc, track_idcs=None, hit_idcs=None, trigger_idcs=None,
                    **kwargs):
        ''' Write an event at row index specified by `loc` '''
        # write event in correct location with uninitialized references
        hit_dset_name = self.type_lookup[reco3d_types.Hit]
        hit_ref = None
        if hit_idcs:
            hit_ref = self.datafile[hit_dset_name].regionref[hit_idcs]
        trigger_dset_name = self.type_lookup[reco3d_types.ExternalTrigger]
        trigger_ref = None
        if trigger_idcs:
            trigger_ref = self.datafile[trigger_dset_name].regionref[trigger_idcs]
        track_dset_name = self.type_lookup[reco3d_types.Track]
        track_ref = None
        if track_idcs:
            track_ref = self.datafile[track_dset_name].regionref[track_idcs]
        event_dset_name = self.type_lookup[type(event)]
        event_data = self.reco3d_type_to_hdf5(event, hit_ref=hit_ref, track_ref=track_ref, **kwargs)
        event_idx = self.write_data(event_dset_name, event_data, loc)

        if not track_idcs is None and not hit_idcs is None and not trigger_idcs:
            return event_idx
        # store hits, tracks, and triggers if none are specified

        event_idcs = [event_idx]
        if hit_ref is None and event.hits:
            hit_idcs = []
            # store hits
            for hit in event.hits:
                hit_idcs += [self.write_hit(hit, None, event_idcs=event_idcs, track_idcs=track_idcs)]
            hit_ref = self.datafile[hit_dset_name].regionref[sorted(hit_idcs)]
            # re-store event
            event_data = self.reco3d_type_to_hdf5(event, hit_ref=hit_ref, track_ref=track_ref,
                                                  trigger_ref=trigger_ref, **kwargs)
            event_idx = self.write_data(event_dset_name, event_data, event_idx)

        if trigger_ref is None and event.triggers:
            trigger_idcs = []
            # store hits
            for trigger in event.triggers:
                trigger_idcs += [self.write_trigger(trigger, None, event_idcs=event_idcs)]
            trigger_ref = self.datafile[trigger_dset_name].regionref[sorted(trigger_idcs)]
            # re-store event
            event_data = self.reco3d_type_to_hdf5(event, hit_ref=hit_ref, track_ref=track_ref,
                                                  trigger_ref=trigger_ref, **kwargs)
            event_idx = self.write_data(event_dset_name, event_data, event_idx)

        if track_idcs is None and event.reco_objs:
            # store tracks
            track_idcs = []
            tracks = [reco_obj for reco_obj in event.reco_objs if isinstance(reco_obj, reco3d_types.Track)]
            if tracks:
                for track in tracks:
                    # find hits associated with track
                    track_hit_idcs = []
                    for hit in track.hits:
                        track_hit_idcs += [self.find(hit, hit_idcs)]
                    track_hit_ref = self.datafile[hit_dset_name].regionref[sorted(track_hit_idcs)]
                    # write track with references
                    track_idx = self.write_track(track, None, event_idcs=event_idcs, hit_idcs=track_hit_idcs)
                    track_idcs += [track_idx]
                    # write hits with new reference
                    hit_track_idcs = [track_idx]
                    for hit_idx, hit in zip(track_hit_idcs, track.hits):
                        self.write_hit(hit, hit_idx, event_idcs=event_idcs, track_idcs=hit_track_idcs)

                    track_ref = self.datafile[track_dset_name].regionref[sorted(track_idcs)]
                    # re-store event
                    event_data = self.reco3d_type_to_hdf5(event, hit_ref=hit_ref,
                                                          track_ref=track_ref,
                                                          trigger_ref=trigger_ref, **kwargs)
                    event_idx = self.write_data(event_dset_name, event_data, event_idx)
        return event_idx

    def write_trigger(self, trigger, loc, event_idcs=None, **kwargs):
        ''' Write a trigger to row index specified by `loc`, returns index of written trigger '''
        hit_dset_name = self.type_lookup[type(trigger)]
        event_ref = None
        if event_idcs:
            event_ref = self.datafile['events'].regionref[event_idcs]
        trigger_data = self.reco3d_type_to_hdf5(trigger, track_ref=track_ref, **kwargs)
        return self.write_data(trigger_dset_name, trigger_data, loc)

    def find(self, obj, search_region=None):
        '''
        Look for objects that match data object at indices specified in search_region.
        Return index of row that matches or None, if it can't be found
        '''
        if not isinstance(obj, tuple(self.type_lookup.keys())):
            return None
        dset_name = self.type_lookup[type(obj)]
        search_idcs = search_region
        region = search_region
        if search_idcs is None:
            # search all data
            search_idcs = range(self.datafile[dset_name].shape[0])
            region = self.datafile[dset_name].regionref[search_idcs]
        elif isinstance(region, (list, slice, tuple)):
            # search by indices
            region = self.datafile[dset_name].regionref[search_idcs]
        else:
            raise ValueError('cannot search with region type')

        for row_idx, row_data in zip(search_idcs, self.datafile[dset_name][region]):
            obj_to_compare = None
            if dset_name == 'hits':
                obj_to_compare = self.hdf5_to_hit(row_data)
            elif dset_name == 'tracks':
                obj_to_compare = self.hdf5_to_track(row_data)
            elif dset_name == 'events':
                obj_to_compare = self.hdf5_to_event(row_data)
            elif dset_name == 'triggers':
                obj_to_compare = self.hdf5_to_trigger(row_data)
            if obj == obj_to_compare:
                return int(row_idx)
        return None
