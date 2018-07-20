import pytest
import h5py
import os
from reco3d.converters.larpix_converters import (region_ref, LArPixHDF5Converter)
from reco3d.tools.options import OptionsTool
from reco3d.types.larpix_types import (Hit, Event, Track)

def test_LArPixHDF5Converter():
    # test init
    opts = OptionsTool({'filename':'test.h5'})
    c = LArPixHDF5Converter(opts)
    assert not c.is_open
    assert c.datafile is None
    assert c.read_idx == {'hits':0, 'events':0, 'tracks':0}
    assert c.write_idx == {'hits':0, 'events':0, 'tracks':0}

    try:
        # test opening file
        c.open()
        assert c.is_open
        assert isinstance(c.datafile, h5py.File)
        for dataset_name in c.rev_type_lookup.keys():
            assert c.write_idx[dataset_name] == 0

        test_hit0 = Hit(1,2,3,4,5)
        test_hit1 = Hit(5,4,3,2,1)
        test_track = Track([test_hit0], 1, 2, 3, 4)
        test_event = Event(1, [test_hit0], reco_objs=[test_track])

        # test writing hit
        c.write(test_hit0)
        c.write(test_hit1)
        assert c.write_idx['hits'] == 2
        assert c.datafile['hits'].shape[0] == 2
        expected = c.reco3d_type_to_hdf5(test_hit0)
        for name in c.datafile['hits'][0].dtype.names:
            if bool(c.datafile['hits'][0][name]):
                # ignore region references
                assert c.datafile['hits'][0][name] == expected[name]
        assert not bool(c.datafile['hits'][0]['track_ref'])
        assert not bool(c.datafile['hits'][0]['event_ref'])

        # test writing track
        c.write(test_track)
        assert c.write_idx['hits'] == 3
        assert c.write_idx['tracks'] == 1
        assert c.datafile['hits'].shape[0] == 3
        assert c.datafile['tracks'].shape[0] == 1
        expected = c.reco3d_type_to_hdf5(test_track)
        for name in c.datafile['tracks'][0].dtype.names:
            if bool(c.datafile['tracks'][0][name]):
                if isinstance(c.datafile['tracks'][0][name], region_ref):
                    # ignore references
                    continue
                else:
                    assert c.datafile['tracks'][0][name] == expected[name]

        # test writing event
        c.write(test_event)
        assert c.write_idx['hits'] == 4
        assert c.write_idx['tracks'] == 2
        assert c.write_idx['events'] == 1
        assert c.datafile['hits'].shape[0] == 4
        assert c.datafile['tracks'].shape[0] == 2
        assert c.datafile['events'].shape[0] == 1
        expected = c.reco3d_type_to_hdf5(test_event)
        for name in c.datafile['events'][0].dtype.names:
            if bool(c.datafile['events'][0][name]):
                if type(c.datafile['events'][0][name]) == region_ref:
                    # ignore references
                    continue
                else:
                    assert c.datafile['events'][0][name] == expected[name]

        # test reading hits
        read_hit0 = c.read(Hit)
        assert c.read_idx['hits'] == 1
        assert read_hit0 == test_hit0
        read_hit1 = c.read(Hit)
        assert c.read_idx['hits'] == 2
        assert read_hit1 == test_hit1
        read_hit3 = c.read(Hit, 0)
        assert read_hit3 == test_hit0
        assert c.read_idx['hits'] == 2

        # test reading tracks
        read_track = c.read(Track)
        assert read_track == test_track
        assert c.read_idx['tracks'] == 1

        # test reading events
        read_event = c.read(Event)
        assert read_event == test_event
        assert c.read_idx['events'] == 1

        c.close()
        assert c.is_open == False

    finally:
        os.remove('test.h5')
