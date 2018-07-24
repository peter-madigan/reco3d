import pytest
import os
import reco3d.types as reco3d_types
from reco3d.converters.larpix_converters import LArPixHDF5Converter
from reco3d.resources.larpix_resources import LArPixDataResource
from reco3d.tools.options import OptionsTool

def test_LArPixDataResource():
    opts = OptionsTool()
    with pytest.raises(RuntimeError, message='should raise error - no converter specified'):
        dr = LArPixDataResource(opts)
        dr.config()
    opts = OptionsTool({'LArPixHDF5Converter' : { 'filename' : 'test.h5' }})
    dr = LArPixDataResource(opts)
    try:
        dr.config()
        assert isinstance(dr.converter, LArPixHDF5Converter)
        dr.start()
        test_hit = reco3d_types.Hit(1,2,3,4,5)
        dr.write(test_hit)
        assert len(dr._write_queue[reco3d_types.Hit]) == 1
        assert dr._write_queue[reco3d_types.Hit][0] == test_hit
        dr.run()
        assert len(dr._write_queue[reco3d_types.Hit]) == 1
        assert dr._write_queue[reco3d_types.Hit][0] == test_hit
        dr.write([test_hit]*100)
        assert len(dr._write_queue[reco3d_types.Hit]) == 101
        assert dr._write_queue[reco3d_types.Hit][100] == test_hit
        assert dr.converter.write_idx['hits'] == 0
        dr.run()
        assert dr.converter.write_idx['hits'] == 101
        assert not dr._write_queue[reco3d_types.Hit]
        dr.write(test_hit)
        dr.finish()
        assert dr.converter.write_idx['hits'] == 102
        dr.cleanup()
    finally:
        os.remove('test.h5')
        
