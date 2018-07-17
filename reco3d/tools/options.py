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

    Creating a child OptionsTool is as easy as calling `grandparent.get('ChildName')`.

    The `'name'` key is a special key that should not be used by objects utilizing an
    options tool.

    When accessing a key, if the key does not exist in the OptionsTool, None is returned.
    '''

    def __init__(self, options_dict={}, name=None, filename=None):
        '''
        Initialize the OptionsTool using a dict or file
        Note: file keys / values take precedence
        '''
        self._opt_dict = options_dict.copy()
        self['name'] = name
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
        if key[0] is '_':
            return
        self._opt_dict[key] = value

    def __len__(self):
        return len(self._opt_dict.keys())

    def __iter__(self):
        return iter(self._opt_dict.keys())

    def __contains__(self, key):
        return key in self._opt_dict.keys()

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        elif any([not key in other for key in self]):
            return False
        elif any([not key in self for key in other]):
            return False
        elif any([self[key] != other[key] for key in self]):
            return False
        return True

    def __str__(self):
        string = ''
        if not 'name' in self or self['name'] is None:
            string += 'OptionsTool(\n'
        else:
            string += self['name'] + '(\n'
        if len(self) == 0:
            string += '\tNone'
        else:
            substrings = []
            for key in self:
                if key is 'name':
                    continue
                elif isinstance(self[key], dict):
                    substrings += ['\t' + str(self.get(key)).replace('\n','\n\t') + ',\n']
                else:
                    substrings += ['\t' + key + ' = ' + self[key] + ',\n']
            string += ''.join(substrings)
        string += '\t)'
        return string


    def get(self, name):
        '''
        Search through options dict for options that match name
        Returns an OptionsTool created from sub dict, with correct name
        '''
        if name in self:
            if isinstance(self[name], dict):
                return OptionsTool(options_dict=self[name], name=name)
            else:
                return OptionsTool()
        else:
            return OptionsTool()

    def set(self, name=None, **kwargs):
        '''
        Set an option value using kwargs
        `name` key provides special access to a sub dict
        '''
        if name is None:
            for key, value in kwargs.items():
                self[key] = value
        else:
            for key, value in kwargs.items():
                try:
                    self[name][key] = value
                except KeyError:
                    self[name] = { key : value }

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
                raise FileNotFoundError

        for key, value in filedata.items():
            self[key] = value
