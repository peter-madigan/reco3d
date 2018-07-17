class OptionsTool(object):
    def __init__(self, options_dict={}):
        self._opt_dict = options_dict.copy()

    def __getitem__(self, option):
        # return option value
        try:
            return self._opt_dict[option]
        except KeyError:
            return None

    def get(self, class_name):
        # search through options dict for class options
        # return new OptionsTool for that dict
        if class_name in self._opt_dict:
            return OptionsTool(self._opt_dict[class_name])
        else:
            return OptionsTool()

    def set(self, class_name=None, **kwargs):
        # set options values
        if class_name is None:
            for key, value in kwargs.items():
                self._opt_dict[key] = value
        else:
            for key, value in kwargs.items():
                try:
                    self._opt_dict[class_name][key] = value
                except KeyError:
                    self._opt_dict[class_name] = { key : value }
