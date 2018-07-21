import pytest
import reco3d.types as reco3d_types
from reco3d.tools.options import OptionsTool
from reco3d.processes.larpix_processes import (LArPixDataReaderProcess)
from tests.test_resources.resources import TestResource

def test_LArPixDataReaderProcess():
    # test initialization and read one hit at a time
    in_resource = TestResource(OptionsTool())
    out_resource = TestResource(OptionsTool())
    process = LArPixDataReaderProcess(OptionsTool(), in_resource=in_resource, out_resource=out_resource)
    with pytest.raises(RuntimeError):
        process.config()
    process.req_resources['in_resource'] += ['TestResource']
    process.req_resources['out_resource'] += ['TestResource']
    in_resource.config()
    out_resource.config()
    process.config()
    test_hit = reco3d_types.Hit(1,2,3,4,5)
    in_resource._read_queue[reco3d_types.Hit] = [test_hit]
    process.run()
    assert not in_resource._read_queue[reco3d_types.Hit]
    assert len(out_resource._stack[reco3d_types.Hit]) == 1
    assert out_resource._stack[reco3d_types.Hit][0] == test_hit
    in_resource.run()
    out_resource.run()

    # make sure it can continue to run
    process.run()

    # test reading multiple hits at a time
    opts = OptionsTool({'max' : 10})
    process = LArPixDataReaderProcess(opts, in_resource=in_resource, out_resource=out_resource)
    process.req_resources['in_resource'] += ['TestResource']
    process.req_resources['out_resource'] += ['TestResource']
    in_resource.config()
    out_resource.config()
    process.config()
    in_resource._read_queue[reco3d_types.Hit] = [test_hit]*11
    process.run()
    assert len(in_resource._read_queue[reco3d_types.Hit]) == 1
    assert len(out_resource._stack[reco3d_types.Hit]) == 10
    in_resource.run()
    out_resource.run()
    process.run()
    assert not in_resource._read_queue[reco3d_types.Hit]
    assert len(out_resource._stack[reco3d_types.Hit]) == 1
    in_resource.run()
    out_resource.run()
    process.run()
    assert not in_resource._read_queue[reco3d_types.Hit]
    assert not reco3d_types.Hit in out_resource._stack
