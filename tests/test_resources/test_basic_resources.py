import pytest
import os
import reco3d.types as reco3d_types
from reco3d.resources.basic_resources import Resource
from reco3d.tools.options import OptionsTool

def test_Resource_read():
    opts = OptionsTool()
    r = Resource(opts)

    test_data = list(range(10))
    r._read_queue[int] = test_data
    assert r.read(float) is None
    read_value = r.read(int)
    assert read_value == 0
    assert len(r._read_queue[int]) == 9
    read_value = r.read(int, n=2)
    assert read_value == [1,2]
    assert len(r._read_queue[int]) == 7
    read_value = r.read(int, n=-1)
    assert read_value == [3,4,5,6,7,8,9]
    assert not r._read_queue[int]
    assert r.read(int) is None

def test_Resource_write():
    opts = OptionsTool()
    r = Resource(opts)

    r.write(10)
    assert r._write_queue[int] == [10]
    r.write([9,8])
    assert r._write_queue[int] == [10,9,8]

def test_Resource_stack():
    opts = OptionsTool()
    r = Resource(opts)

    assert r.pop(int) is None
    assert r.peek(int) is None
    
    test_data = list(range(10))
    r.push(test_data[0])
    assert r._stack[int] == [0]
    r.push(test_data[1:])
    assert r._stack[int] == test_data

    assert r.pop(int) == 9
    assert r.pop(int, n=2) == [8,7]
    assert r.peek(int) == 6
    assert len(r._stack[int]) == 7
    assert r.peek(int, n=2) == [6,5]
    assert len(r._stack[int]) == 7
    assert r.peek(int, n=-1) == [6,5,4,3,2,1,0]
    assert len(r._stack[int]) == 7
    assert r.pop(int, n=-1) == [6,5,4,3,2,1,0]
    assert not r._stack[int]

    r.push(test_data)
    r.purge(dtype=int)
    assert r.peek(int) is None
    r.push(test_data)
    r.purge(dtype=float)
    assert r.peek(int) == 9
    r.push(test_data)
    r.purge()
    assert r.pop(int) is None

    test_floats = [0.0, 1.0, 2.0]
    r.push(test_data)
    r.push(test_floats)
    assert r.peek(float) == 2.0
    r.preserve(int)
    r.run()
    assert r.peek(float) is None
    assert r.peek(int) == 9
    r.run()
    assert r.peek(int) is None
