import pytest
import reco3d.types as reco3d_types
from reco3d.tools.options import OptionsTool
from reco3d.processes.larpix_processes import (LArPixDataReaderProcess, LArPixEventBuilderProcess, LArPixTriggerBuilderProcess)
from tests.test_resources.resources import TestResource

def test_LArPixDataReaderProcess():
    # test initialization and read one hit at a time
    in_resource = TestResource(OptionsTool())
    out_resource = TestResource(OptionsTool())
    process = LArPixDataReaderProcess(OptionsTool(), in_resource=in_resource, out_resource=out_resource)
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

def test_LArPixEventBuilderProcess():
    test_event = [reco3d_types.Hit(0,1,2,3,4,5)]*10
    test_non_event = [reco3d_types.Hit(1e4,2e4,3e4,4e4,5e4)]
    test_data = test_non_event + test_event + test_non_event + test_event + test_non_event
    dr = TestResource(OptionsTool())
    eb = LArPixEventBuilderProcess(OptionsTool(), active_resource=dr, out_resource=dr)
    dr.config()
    eb.config()
    dr.start()
    eb.start()
    dr.push(test_data)
    eb.run()
    event0 = dr.peek(reco3d_types.Event)
    assert event0.nhit == 10
    assert event0.ts_start == 3
    assert len(dr.peek(reco3d_types.Event, n=-1)) == 2

def test_LArPixTriggerBuilderProcess():
    test_trigger = [reco3d_types.Hit(0,1,2,3,4,5,chipid,0) for chipid in range(10)]
    test_nontrigger = [reco3d_types.Hit(1e4,2e4,3e4,4e4,5e4)]
    test_data = test_nontrigger + test_trigger + test_nontrigger + test_trigger + test_nontrigger
    dr = TestResource(OptionsTool())
    tb = LArPixTriggerBuilderProcess(\
        OptionsTool({'channel_mask': dict([(chipid,[0]) for chipid in range(10)])}),
        active_resource=dr, out_resource=dr)

    dr.config()
    tb.config()
    dr.start()
    tb.start()
    dr.push(test_data)
    tb.run()
    trigger0 = dr.peek(reco3d_types.ExternalTrigger)
    assert trigger0.ts == 3
    assert len(dr.peek(reco3d_types.ExternalTrigger, n=-1)) == 2

def test_LArPixEventBuilderAssociation():
    test_data = []

    ts = 0
    test_event = [reco3d_types.Hit(hid,px=0,py=0,ts=ts,q=1) for hid in range(10)]
    test_data += test_event

    ts += 500e3 # ns
    test_nonevent = [reco3d_types.Hit(10+hid,px=0,py=0,ts=ts,q=1) for hid in range(3)]
    test_data += test_nonevent

    ts += 497e3 # ns
    test_trigger = [reco3d_types.Hit(13+chipid,px=0,py=0,ts=ts,q=1,iochain=None,chipid=chipid,
                                     channelid=0)
                    for chipid in range(10)]
    test_data += test_trigger

    ts += 10e3 # ns
    test_nonevent = [reco3d_types.Hit(23+hid,px=0,py=0,ts=ts,q=1) for hid in range(3)]
    test_data += test_nonevent

    dr = TestResource(OptionsTool())
    tb = LArPixTriggerBuilderProcess(\
        OptionsTool({'channel_mask': dict([(chipid,[0]) for chipid in range(10)])}),
        active_resource=dr, out_resource=dr)
    eb = LArPixEventBuilderProcess(OptionsTool({'associate_triggers':True}), active_resource=dr, out_resource=dr)

    dr.config()
    tb.config()
    eb.config()
    dr.start()
    tb.start()
    eb.start()
    dr.push(test_data)
    tb.run()
    eb.run()

    events = dr.peek(reco3d_types.Event, n=-1)
    triggers = dr.peek(reco3d_types.ExternalTrigger, n=-1)
    assert len(events) == 1
    assert len(triggers) == 1
    assert len(events[0].triggers) == 1
    assert events[0].triggers[0].ts == 997e3
    assert events[0].triggers[0].delay == 997e3
