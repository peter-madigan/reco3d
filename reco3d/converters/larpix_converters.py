'''
This module contains converters used by LArPix reconstruction and analysis

The module requirements are `h5py` and `numpy`.

'''
from reco3d.converters.basic_converters import Converter
import reco3d.tools.python as reco3d_pytools
import reco3d.types as reco3d_types
import h5py
import numpy as np

region_ref = h5py.special_dtype(ref=h5py.RegionReference)

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
            ('nhit', 'i8'), ('q', 'i8'), ('ts_start', 'i8'), ('ts_end', 'i8')],
        'tracks' : [
            ('track_id','i8'), ('event_ref', region_ref), ('hit_ref', region_ref),
            ('theta', 'f8'),
            ('phi', 'f8'), ('xp', 'f8'), ('yp', 'f8'), ('nhit', 'i8'),
            ('q', 'i8'), ('ts_start', 'i8'), ('ts_end', 'i8'),
            ('sigma_theta', 'f8'), ('sigma_phi', 'f8'), ('sigma_x', 'f8'),
            ('sigma_y', 'f8')],
        }

    def __init__(self, options):
        super(LArPixHDF5Converter, self).__init__(options)
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
        if not dtype in self.type_lookup: return None
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

        return False

    def create_dataset(self, name):
        '''
        Initialize a dataset with name
        '''
        if not name in self.datafile.keys():
            self.datafile.create_dataset(name, (0,), maxshape=(None,),
                                         dtype=self.dataset_desc[name])

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
        hit = self.hdf5_to_reco3d_type(reco3d_types.Hit, data)
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
        track = self.hdf5_to_reco3d_type(reco3d_types.Track, data)
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
        event = self.hdf5_to_reco3d_type(reco3d_types.Event, data)
        return event

    def write_obj(self, obj, loc, **kwargs):
        '''
        Write an object to a particular location
        If loc is larger than current array size, resize array accordingly
        Returns row index of object
        '''
        write_data = self.reco3d_type_to_hdf5(obj, **kwargs)
        if write_data is None:
            raise TypeError('could not convert data type to array')
        dset_name = self.type_lookup[type(obj)]

        if not dset_name in self.datafile.keys():
            self.create_dataset(dset_name)

        write_idx = loc
        if write_idx is None:
            write_idx = self.write_idx[dset_name]
            self.write_idx[dset_name] += 1

        if self.datafile[dset_name].shape[0] <= write_idx:
            self.datafile[dset_name].resize(write_idx + 1, axis=0)

        self.datafile[dset_name][write_idx] = write_data
        return write_idx

    def write_hit(self, hit, loc, event_ref=None, track_ref=None):
        ''' Write a hit to row index specified by `loc` '''
        return self.write_obj(hit, loc, event_ref=event_ref, track_ref=track_ref)

    def write_track(self, track, loc, event_ref=None, hit_ref=None):
        ''' Write a track at row index specified by `loc` '''
        # write track in correct location with uninitialized references
        track_dset_name = self.type_lookup[type(track)]
        track_idx = loc
        if loc is None:
            track_idx = self.write_idx[track_dset_name]
            self.write_idx[track_dset_name] += 1
        track_idx = self.write_obj(track, track_idx, event_ref=event_ref, hit_ref=hit_ref)
        track_ref = self.datafile[track_dset_name].regionref[track_idx]

        if not hit_ref is None:
            return track_idx
        # store hits if no hit_ref is given

        if hit_ref is None and track.hits:
            # store hits
            hit_idcs = []
            for hit in track.hits:
                hit_idcs += [self.write_hit(hit, None, event_ref=None, track_ref=track_ref)]
            hit_dset_name = self.type_lookup[type(track.hits[0])]
            if track.hits:
                hit_ref = self.datafile[hit_dset_name].regionref[hit_idcs]
            else:
                hit_ref = None
            # re-store track
            track_idx = self.write_obj(track, track_idx, event_ref=event_ref, hit_ref=hit_ref)

        return track_idx
    
    def write_event(self, event, loc, track_ref=None, hit_ref=None):
        ''' Write an event at row index specified by `loc` '''
        # write event in correct location with uninitialized references
        event_dset_name = self.type_lookup[type(event)]
        event_idx = loc
        if event_idx is None:
            event_idx = self.write_idx[event_dset_name]
            self.write_idx[event_dset_name] += 1
        event_idx = self.write_obj(event, event_idx, track_ref=track_ref, hit_ref=hit_ref)
        event_ref = self.datafile[event_dset_name].regionref[event_idx]

        if not track_ref is None and not hit_ref is None:
            return event_idx
        # store hits and tracks if none are specified

        if hit_ref is None:
            # store hits
            hit_idcs = []
            for hit in event.hits:
                hit_idcs += [self.write_hit(hit, None, event_ref=event_ref, track_ref=track_ref)]
            hit_dset_name = self.type_lookup[type(event.hits[0])]
            if event.hits:
                hit_ref = self.datafile[hit_dset_name].regionref[hit_idcs]
            else:
                hit_ref = None
            # re-store event
            event_idx = self.write_obj(event, event_idx, track_ref=track_ref, hit_ref=hit_ref)

        if track_ref is None:
            # store tracks
            track_idcs = []
            tracks = [reco_obj for reco_obj in event.reco_objs if isinstance(reco_obj, reco3d_types.Track)]
            if tracks and track_ref is None:
                track_dset_name = self.type_lookup[type(tracks[0])]
                for track in tracks:
                    # find hits associated with track
                    hit_idcs = []
                    for hit in track.hits:
                        hit_idcs += [self.find(hit, hit_ref)]
                    track_hit_ref = self.datafile[hit_dset_name].regionref[hit_idcs]
                    # write track with references
                    track_idx = self.write_obj(track, None, event_ref=event_ref, hit_ref=track_hit_ref)
                    track_idcs += [track_idx]
                    # write hits with references
                    hit_track_ref = self.datafile[track_dset_name].regionref[track_idx]
                    for hit_idx, hit in zip(hit_idcs, track.hits):
                        self.write_hit(hit, hit_idx, event_ref=event_ref, track_ref=hit_track_ref)
            if tracks:
                track_ref = self.datafile[track_dset_name].regionref[track_idcs]
            else:
                track_ref = None
            # re-store event
            event_idx = self.write_obj(event, event_idx, track_ref=track_ref, hit_ref=hit_ref)
        return event_idx

    def find(self, obj, search_region=None):
        '''
        Look for objects that match data object in a region.
        Return index of row that matches or None, if it can't be found
        '''
        if not isinstance(obj, tuple(self.type_lookup.keys())):
            return None
        dset_name = self.type_lookup[type(obj)]
        region = search_region
        if region is None:
            # search all data
            region = self.datafile[dset_name].regionref[:]
        elif isinstance(region, (list, slice, int)):
            # search by indices
            region = self.datafile[dset_name].regionref[search_region]
        elif isinstance(region, h5py.RegionReference):
            # search by reference
            region = region
        else:
            raise ValueError('cannot search with region type')

        for row_idx, row_data in enumerate(self.datafile[dset_name][region]):
            obj_data = self.hdf5_to_reco3d_type(type(obj), row_data)
            if obj_data == obj:
                return row_idx
        return None

    def reco3d_type_to_hdf5(self, reco3d_type_obj, **kwargs):
        '''
        Automatically generate numpy array used by hdf5
        Additional attributes can be set (or overridden by kwargs)
        '''
        if not isinstance(reco3d_type_obj, tuple(self.type_lookup.keys())):
            return None
        data_dict = vars(reco3d_type_obj).copy()
        dataset_name = self.type_lookup[type(reco3d_type_obj)]
        for value_name, value in kwargs.items():
            data_dict[value_name] = value
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

    def hdf5_to_reco3d_type(self, dtype, data):
        '''
        Convert a numpy array into a reco3d type, building references as well
        '''
        if not dtype in self.type_lookup.keys():
            return None
        dset_name = self.type_lookup[dtype]
        args_dict = {}
        for key in data.dtype.names:
            args_dict[key] = data[key]
        items_to_add = []
        for key, value in args_dict.items():
            if dset_name != 'hits' and isinstance(value, h5py.RegionReference) and value:
                region = self.datafile[value][value]
                if key == 'hit_ref':
                    items_to_add += [('hits', [self.hdf5_to_reco3d_type(\
                                    reco3d_types.Hit, hit_row) for hit_row in region])]
                elif key == 'track_ref':
                    items_to_add += [('reco_objs', [self.hdf5_to_reco3d_type(\
                            reco3d_types.Track, track_row) for track_row in region])]
        for key, value in items_to_add:
            args_dict[key] = value
        self.replace_default_with_none(args_dict)
        obj = (dtype)(**args_dict)
        return obj

    @classmethod
    def replace_default_with_none(cls, args_dict):
        '''
        Fill all instances of -9999 with None
        '''
        for key, value in args_dict.items():
            if value == -9999:
                args_dict[key] = None
