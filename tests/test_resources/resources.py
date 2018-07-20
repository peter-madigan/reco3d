'''
This module contains a Resource class useful in testing
Note that this file is skipped by pytest

'''
import reco3d.tools.python as reco3d_pytools
import reco3d.types as reco3d_types
from reco3d.resources.basic_resources import Resource

class TestResource(Resource):
    req_opts = Resource.req_opts + []
    default_opts = reco3d_pytools.combine_dicts(
        Resource.default_opts, { 'max_reads' : 100 }) # only perform this number of reads (None, doesn't halt reading)

    def config(self):
        super().config()

        self.max_reads = self.options['max_reads']
        self.read_counter = 0

    def continue_run(self):
        parent_result = super().continue_run()
        if self.max_reads is None:
            return parent_result
        return (not self.read_counter > self.max_reads) and parent_result
