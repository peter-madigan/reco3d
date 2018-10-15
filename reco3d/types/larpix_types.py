'''
This module contains primitive data types used by the LArPix reconstruction
'''
import numpy as np

class ExternalTrigger(object):
    ''' A basic primitive type to store external trigger information '''

    def __init__(self, trig_id, ts, delay=0, type=None):
        self.trig_id = trig_id
        self.ts = ts
        self.delay = delay
        self.trig_type = type

    def __str__(self):
        string = 'ExternalTrigger(trig_id={trig_id}, ts={ts}, delay={delay}, '\
            'type={trig_type})'.format(**vars(self))
        return string

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class Hit(object):
    ''' The basic primitive type used in larpix-reconstruction represents a single trigger of a larpix channel '''

    def __init__(self, hid, px, py, ts, q, iochain=None, chipid=None, channelid=None, geom=None, **kwargs):
        self.hid = hid
        self.px = px
        self.py = py
        self.ts = ts
        self.q = q
        self.iochain = iochain
        self.chipid = chipid
        self.channelid = channelid
        self.geom = geom

    def __str__(self):
        string = 'Hit(hid={hid}, px={px}, py={py}, ts={ts}, q={q}, iochain={iochain}, '\
            'chipid={chipid}, channelid={channelid}, geom={geom})'.format(**vars(self))
        return string

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class HitCollection(object):
    ''' A base class of collected `Hit` types '''
    def __init__(self, hits, **kwargs):
        self.hits = hits
        self.nhit = len(self.hits)
        if self.nhit > 0:
            self.ts_start = min(self.get_hit_attr('ts'))
            self.ts_end = max(self.get_hit_attr('ts'))
            self.q = sum(self.get_hit_attr('q'))
        else:
            self.ts_start = None
            self.ts_end = None
            self.q = None

    def __str__(self):
        string = '{}(hits=[\n\t{}]\n\t)'.format(self.__class__.__name__, \
            ', \n\t'.join(str(hit) for hit in self.hits))
        return string

    def __getitem__(self, key):
        '''
        Access to hits or hit attr.
        If key is an int -> returns hit at that index
        If key in a str -> returns attr value of all hits specified by key
        If key is a dict -> returns hits with attr values that match dict
        If key is a list or tuple -> returns hits at indices
        E.g.
        hc = HitCollection(hits=[Hit(0,0,0,0), Hit(1,0,0,0), Hit(1,1,0,0)])
        hc[0] # Hit(0,0,0,0)
        hc['px'] # [0,1,1]
        hc[{'px' : 1}] # [Hit(1,0,0,0), Hit(1,1,0,0)]
        hc[0,1] # [Hit(0,0,0,0), Hit(1,0,0,0)]
        '''
        if isinstance(key, int):
            return self.hits[key]
        elif isinstance(key, str):
            return self.get_hit_attr(key)
        elif isinstance(key, dict):
            return self.get_hit_match(key)
        elif isinstance(key, (list, tuple)):
            return [self.hits[idx] for idx in key]

    def __len__(self):
        return nhit

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for key, value in self.__dict__.items():
            if isinstance(value, np.ndarray):
                if not len(value) == getattr(other, key):
                    return False
                elif not (all([self_value in getattr(other, key) for self_value in value])
                          and all([other_value in value for other_value in getattr(other, key)])):
                    return False
            else:
                if not value == getattr(other, key):
                    return False
        return True

    def get_hit_attr(self, attr, default=None):
        ''' Get a list of the specified attribute from event hits '''
        if not default is None:
            return [getattr(hit, attr, default) for hit in self.hits]
        return [getattr(hit, attr) for hit in self.hits]

    def get_hit_match(self, attr_value_dict):
        '''
        Returns a list of hits that match the attr_value_dict
        attr_value_dict = { <hit attribute> : <value of attr>, ...}
        '''
        return_list = []
        for hit in self.hits:
            if all([getattr(hit, attr) == value for attr, value in \
                        attr_value_dict.items()]):
                return_list += [hit]
        return return_list

class Event(HitCollection):
    '''
    A class for a collection of hits associated by the event builder, contains
    reconstructed objects
    '''
    def __init__(self, evid, hits, triggers=None, reco_objs=None, **kwargs):
        super().__init__(hits)
        self.evid = evid
        if triggers is None:
            self.triggers = []
        else:
            self.triggers = triggers
        if reco_objs is None:
            self.reco_objs = []
        else:
            self.reco_objs = reco_objs

    def __str__(self):
        string = HitCollection.__str__(self)[:-1]
        string += ', evid={evid}, triggers={triggers}, reco_objs={reco_objs})'.format(\
            **vars(self))
        return string

class Track(HitCollection):
    '''
    A class representing a reconstructed straight line segment and associated
    hits
    '''
    def __init__(self, hits, theta, phi, xp, yp, vertices=None, cov=None, **kwargs):
        super().__init__(hits)
        self.theta = theta
        self.phi = phi
        self.xp = xp
        self.yp = yp
        if vertices is None:
            self.vertices = []
        else:
            self.vertices = vertices
        self.cov = cov

    def __str__(self):
        string = HitCollection.__str__(self)[:-1]
        string += ', theta={theta}, phi={phi}, xp={xp}, yp={yp}, vertices={vertices},'\
            ' cov={cov})'.format(**vars(self))
        return string


class Shower(HitCollection):
    ''' A class representing a shower '''
    pass
# etc
