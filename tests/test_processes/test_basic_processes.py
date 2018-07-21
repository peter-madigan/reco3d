import pytest
from tests.test_resources.resources import TestResource
from reco3d.processes.basic_processes import Process
from reco3d.tools.options import OptionsTool

def test_Process_init():
    resource0 = TestResource(OptionsTool())
    resource1 = TestResource(OptionsTool())
    resource2 = TestResource(OptionsTool())
    Process.opt_resources = {'opt_resource' : ['TestResource']}
    Process.req_resources = {'req_resource' : ['TestResource'], 'missing_resource' : ['TestResource']}
    process = Process(OptionsTool(), opt_resource=resource0, req_resource=resource1)
    with pytest.raises(RuntimeError, message='should fail - missing a resource'):
        process.config()
    process = Process(OptionsTool(), opt_resource=resource0, req_resource=resource1, missing_resource=resource2)
    assert process.resources['opt_resource'] == resource0
    assert process.resources['req_resource'] == resource1
    assert process.resources['missing_resource'] == resource2

    process.config()
    process.run()
    process.continue_run()
    process.finish()
    process.cleanup()
