'''
This module contains a variety of useful functions that you may need
to make python do what you want

Contains:
 - `combine_dicts(first_dict, second_dict)`: create new dict that is a copy of `first_dict`,
 overwritten by `second_dict`
'''

def combine_dicts(first_dict, second_dict):
    ''' Overwrite first_dict with keys and values of second_dict '''
    new_dict = first_dict.copy()
    for key, value in second_dict.items():
        new_dict[key] = value
    return new_dict
