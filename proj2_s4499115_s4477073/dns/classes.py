#!/usr/bin/env python2

""" DNS CLASS and QCLASS values

This module contains an Enum of CLASS and QCLASS values. The Enum also contains
a method for converting values to strings. See sections 3.2.4 and 3.2.5 of RFC
1035 for more information.
"""


class Class(object):
    """ Enum of CLASS and QCLASS values
    
    Usage:
        >>> Class.IN
        1
        >>> Class.ANY
        255
    """

    IN = 1
    CS = 2
    CH = 3
    HS = 4
    ANY = 255

    by_string = {
        "IN": IN,
        "CS": CS,
        "CH": CH,
        "HS": HS,
        "*": ANY
    }

    by_value = dict([(y, x) for x, y in by_string.items()])

    @staticmethod
    def to_string(class_):
        return Class.by_value[class_]

    @staticmethod
    def from_string(string):
        return Class.by_string[string]
