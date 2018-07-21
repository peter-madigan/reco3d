import json
import os

CONF_DIR = '../../conf/' # relative path to configuration files

class OptionsTool(object):
    '''
    Class for handling option setting and loading

    Typically a parent OptionsTool is initialized using a filepath or a specified
    json config file in the `conf/` directory. Child options tools can then be
    declared in the configuration file using dict objects with a key reference
    corresponding to the object that will use those options. This allows objects to
    contain sub-objects that can be configured using child OptionsTools.

    Creating a child OptionsTool is as easy as calling `parent.get('ChildName')`.

    When accessing a key, if the key does not exist in the OptionsTool, None is returned.
    '''

    def __init__(self, options_dict={}, filename=None):
        '''
        Initialize the OptionsTool using a dict or file
        Note: file keys / values take precedence
        '''
        self._opt_dict = options_dict.copy()
        if not filename is None:
            self._load_from_file(filename)

    def __getitem__(self, option):
        '''
        Return the value associated with option key
        If option key points to sub dict, returns that dict
        If you want to access a sub dict as another instance of an OptionsTool,
        use the `get()` method
        '''
        # return option value
        try:
            return self._opt_dict[option]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        '''
        ignores all keys starting with _
        '''
        if key[0] == '_':
            return
        self._opt_dict[key] = value

    def __len__(self):
        return len(self._opt_dict.keys())

    def __iter__(self):
        return iter(self._opt_dict.keys())

    def __contains__(self, key):
        return key in self._opt_dict.keys()

    def __eq__(self, other):
        if not isinstance(self, type(other)):
            return False
        elif any([not key in other for key in self]):
            return False
        elif any([not key in self for key in other]):
            return False
        elif any([self[key] != other[key] for key in self]):
            return False
        return True

    def check_req(self, req_opts):
        '''
        Raise RunTimeError if OptionsTool does not contain all `req_opts`
        '''
        if not all([opt_key in self for opt_key in req_opts]):
            raise RuntimeError('missing required options')

    def set_default(self, default_opts):
        '''
        Write default values into options
        '''
        for key, value in default_opts.items():
            if self[key] is None:
                self[key] = value

    def get(self, key):
        '''
        Search through options dict for options that match key
        Also apply option inheritance (propogate higher level options to lower
        levels)
        Returns an OptionsTool created from sub dict, with correct key
        '''
        inherit_opts_dict = self._opt_dict.copy()
        options_dict = None
        if key in self:
            if isinstance(self[key], dict):
                options_dict = self[key]
        if not options_dict is None:
            for new_key, new_value in options_dict.items():
                inherit_opts_dict[new_key] = new_value
        return OptionsTool(options_dict=inherit_opts_dict)

    def set(self, key=None, **kwargs):
        '''
        Set an option value using kwargs
        `key` key provides special access to a sub dict
        '''
        if key is None:
            for arg, value in kwargs.items():
                self[arg] = value
        else:
            for arg, value in kwargs.items():
                try:
                    self[key][arg] = value
                except KeyError:
                    self[key] = { arg : value }

    def _load_from_file(self, filename):
        '''
        Overwrite options dict using a json file
        Searches cwd first, then searches in conf/ directory
        '''
        filedata = {}
        if os.path.exists(filename):
            with open(filename) as infile:
                filedata = json.load(infile)
        else:
            rel_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                    CONF_DIR + filename)
            if os.path.exists(rel_path):
                with open(rel_path) as infile:
                    filedata = json.load(infile)
            else:
                raise FileNotFoundError('could not find configuration file')

        for key, value in filedata.items():
            self[key] = value
