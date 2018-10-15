import pytest
import h5py
import numpy as np
import os
from reco3d.converters.larpix_converters import (region_ref, LArPixHDF5Converter, LArPixSerialConverter)
from reco3d.tools.options import OptionsTool
from reco3d.types.larpix_types import (Hit, Event, Track)

def test_LArPixHDF5Converter():
    # test init
    opts = OptionsTool({'filename':'test.h5'})
    c = LArPixHDF5Converter(opts)
    assert not c.is_open
    assert c.datafile is None
    assert c.read_idx == {'hits':0, 'events':0, 'tracks':0, 'triggers':0}
    assert c.write_idx == {'hits':0, 'events':0, 'tracks':0, 'triggers':0}

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
                if type(c.datafile['tracks'][0][name]) == region_ref:
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
        c.logger.debug(read_track)
        c.logger.debug(test_track)
        assert read_track == test_track
        assert c.read_idx['tracks'] == 1

        # test reading events
        read_event = c.read(Event)
        assert read_event == test_event
        assert c.read_idx['events'] == 1

        c.close()
        assert not c.is_open

    finally:
        os.remove('test.h5')

def test_LArPixSerialConverter():
    # test init
    opts = OptionsTool({'filename':'test.h5'})
    c = LArPixSerialConverter(opts)
    assert not c.is_open
    assert c.datafile is None
    assert c.read_idx == 0

    try:
        # test opening file
        c.open()
        assert c.is_open
        assert isinstance(c.datafile, h5py.File)

        test_data0 = np.array(list(range(max(c._name_lookup.keys())+1)), dtype=np.int64)
        test_data1 = np.array(list(reversed(range(max(c._name_lookup.keys())+1))), dtype=np.int64)
        test_data = np.vstack([test_data0, test_data1])
        c.datafile.create_dataset('data', data=test_data)

        # test reading data
        assert c.read(int) is None
        read0 = c.read(Hit)
        assert c.read_idx == 1
        assert read0.channelid == test_data0[c._col_lookup['channelid']]
        assert read0.chipid == test_data0[c._col_lookup['chipid']]
        assert read0.px == test_data0[c._col_lookup['pixelx']]
        assert read0.py == test_data0[c._col_lookup['pixely']]
        assert read0.ts == test_data0[c._col_lookup['timestamp']]
        read1 = c.read(Hit)
        assert c.read_idx == 2
        assert read1.channelid == test_data1[c._col_lookup['channelid']]
        assert read1.chipid == test_data1[c._col_lookup['chipid']]
        assert read1.px == test_data1[c._col_lookup['pixelx']]
        assert read1.py == test_data1[c._col_lookup['pixely']]
        assert read1.ts == test_data1[c._col_lookup['timestamp']]
        assert c.read(Hit) is None
        assert c.read(Hit, loc=0) == read0

        # test writing data
        assert not c.write(int)
        assert not c.write(Hit(0,1,2,3,4,5))

        # test close
        c.close()
        assert not c.is_open
    finally:
        os.remove('test.h5')
