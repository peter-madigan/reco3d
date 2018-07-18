import pytest
from reco3d.tools.options import OptionsTool
from reco3d.tools.logging import LoggingTool

def test_LoggingTool_def_init(capsys):
    opts = OptionsTool(options_dict={})
    logger = LoggingTool(opts, name='test')
    assert logger.name == 'test'
    assert len(logger.handlers) == 1
    assert logger.level == LoggingTool.default_opts['level']
    assert logger.format == LoggingTool.default_opts['format']
    out, err = capsys.readouterr()
    logger.info('test')
    out, err = capsys.readouterr()
    assert out[-11:-1] == 'test: test'
    assert err == ''
