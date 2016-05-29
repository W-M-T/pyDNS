#!/usr/bin/env python2

""" DNS RCODE values

This module contains an Enum of RCODE values. See section 4.1.4 of RFC 1035 for
more info.
"""

class RCode(object):
    """ Enum of RCODE values
    
    Usage:
        >>> NoError
        0
        >>> NXDomain
        3
    """

    NoError = 0
    FormErr = 1
    ServFail = 2
    NXDomain = 3
    NotImp = 4
    Refused = 5
    YXDomain = 6
    YXRRSet = 7
    NXRRSet = 8
    NotAuth = 9
    NotZone = 10
    BADVERS = 16
    BADSIG = 16
    BADKEY = 17
    BADTIME = 18
    BADMODE = 19
    BADNAME = 20
    BADALG = 21
    BADTRUNC = 22

    by_string = {
        "NoError": NoError,
        "FormErr": FormErr,
        "ServFail": ServFail,
        "NXDomain": NXDomain,
        "NotImp": NotImp,
        "Refused": Refused,
        "YXDomain": YXDomain,
        "YXRRSet": YXRRSet,
        "NXRRSet": NXRRSet,
        "NotAuth": NotAuth,
        "NotZone": NotZone,
        "BADVERS": BADVERS,
        "BADSIG": BADSIG,
        "BADKEY": BADKEY,
        "BADTIME": BADTIME,
        "BADMODE": BADMODE,
        "BADNAME": BADNAME,
        "BADALG": BADALG,
        "BADTRUNC": BADTRUNC
    }

    by_value = dict([(y, x) for x, y in by_string.items()])

    @staticmethod
    def to_string(rcode):
        return RCode.by_value[rcode]

    @staticmethod
    def from_string(string):
        return RCode.by_string[string]
