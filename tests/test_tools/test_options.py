import pytest
from reco3d.tools.options import OptionsTool

def test_OptionsTool_init():
    test_dict = {'a' : 0, 'b' : 1}
    ot = OptionsTool(options_dict=test_dict, name='test')
    assert ot['a'] == 0 and ot['b'] == 1
    assert ot['name'] == 'test'
    assert ot.get('a') == OptionsTool()

def test_OptionsTool_file_init():
    test_dict = {'a' : 0, 'test_overwrite' : 1}
    ot = OptionsTool(options_dict=test_dict, filename='test_conf.json')
    assert ot['name'] is None
    assert not '_test_hidden' in ot
    assert ot['_test_hidden'] is None
    assert ot['a'] == 0
    assert ot['test_key0'] == 'test_value0'
    assert ot['test_overwrite'] == 'new_value'
    assert type(ot['test_named_obj']) is dict
    assert type(ot.get('test_named_obj')) is OptionsTool
    obj_options = ot.get('test_named_obj')
    assert obj_options['name'] == 'test_named_obj'
    assert obj_options['test_key1'] == 'test_value1'
    subobj_options = obj_options.get('test_named_subobj')
    assert subobj_options['name'] == 'test_named_subobj'
    assert subobj_options['test_key2'] == 'test_value2'
    assert subobj_options['test_int'] == 100
    assert subobj_options['test_float'] == 1.0
    assert subobj_options['test_list'] == [0,1,2,3]
    assert subobj_options['test_dict'] == {'a':0, 'b':1}

