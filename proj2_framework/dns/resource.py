#!/usr/bin/env python2

""" A DNS resource record

This class contains classes for DNS resource records and record data. This
module is fully implemented. You will have this module in the implementation
of your resolver and server.
"""

import socket
import struct

from dns.classes import Class
from dns.types import Type


class ResourceRecord(object):
    """ DNS resource record """
    def __init__(self, name, type_, class_, ttl, rdata, timestamp = 0):
        """ Create a new resource record

        Args:
            name (str): domain name
            type_ (Type): the type
            class_ (Class): the class
            rdata (RecordData): the record data
            timestamp (long int): epoch time to which the ttl is relative
            needs to be equal to current time when the record is sent over the internet,
            because the timestamp is not sent
        """
        self.name     = name
        self.type_    = type_
        self.class_   = class_
        self.ttl      = ttl
        self.rdata    = rdata
        self.timestamp = timestamp#Set to zero if not provided, so it will expire immediately when put in the cache

    def to_bytes(self, offset, composer):
        """ Convert ResourceRecord to bytes """
        name = composer.to_bytes(offset, [self.name])
        offset += len(name) + 10
        rdata = self.rdata.to_bytes(offset, composer)
        return (name +
            struct.pack("!HHIH",
                self.type_,
                self.class_,
                self.ttl,
                len(rdata)) + 
            rdata)

    @classmethod
    def from_bytes(cls, packet, offset, parser):
        """ Convert ResourceRecord from bytes """
        names, offset = parser.from_bytes(packet, offset, 1)
        name = names[0]
        type_, class_, ttl, rdlength = struct.unpack_from("!HHIH", packet, offset)
        offset += 10
        rdata = RecordData.from_bytes(type_, packet, offset, rdlength, parser)
        offset += rdlength
        return cls(name, type_, class_, ttl, rdata), offset


class RecordData(object):
    """ Record Data """

    def __init__(self, data):
        """ Initialize the record data

        Args:
            data (str): data
        """
        self.data = data

    @staticmethod
    def create(type_, data):
        """ Create a RecordData object from bytes

        Args:
            type_ (Type): type
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        classdict = {
            Type.A: ARecordData,
            Type.CNAME: CNAMERecordData,
            Type.NS: NSRecordData,
            Type.AAAA: AAAARecordData
        }
        if type_ in classdict:
            return classdict[type_](data)
        else:
            return GenericRecordData(data)

    @staticmethod
    def from_bytes(type_, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            type_ (Type): type
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        classdict = {
            Type.A: ARecordData,
            Type.CNAME: CNAMERecordData,
            Type.NS: NSRecordData,
            Type.AAAA: AAAARecordData
        }
        if type_ in classdict:
            return classdict[type_].from_bytes(
                packet, offset, rdlength, parser)
        else:
            return GenericRecordData.from_bytes(
                packet, offset, rdlength, parser)


class ARecordData(RecordData):
    def to_bytes(self, offset, composer):
        """ Convert to bytes

        Args:
            offset (int): offset in message
            composer (Composer): domain name composer
        """
        return socket.inet_aton(self.data)

    @classmethod
    def from_bytes(cls, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        data = socket.inet_ntoa(packet[offset:offset+4])
        return cls(data)


class CNAMERecordData(RecordData):
    def to_bytes(self, offset, composer):
        """ Convert to bytes

        Args:
            offset (int): offset in message
            composer (Composer): domain name composer
        """
        return composer.to_bytes(offset, [self.data])

    @classmethod
    def from_bytes(cls, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        names, offset = parser.from_bytes(packet, offset, 1)
        data = names[0]
        return cls(data)


class NSRecordData(RecordData):
    def to_bytes(self, offset, composer):
        """ Convert to bytes

        Args:
            offset (int): offset in message
            composer (Composer): domain name composer
        """
        return composer.to_bytes(offset, [self.data])

    @classmethod
    def from_bytes(cls, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        names, offset = parser.from_bytes(packet, offset, 1)
        data = names[0]
        return cls(data)


class AAAARecordData(RecordData):
    def to_bytes(self, offset, composer):
        """ Convert to bytes

        Args:
            offset (int): offset in message
            composer (Composer): domain name composer
        """
        return socket.inet_pton(socket.AF_INET6, self.data)

    @classmethod
    def from_bytes(cls, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        data = socket.inet_ntop(socket.AF_INET6, packet[offset:offset+16])
        return cls(data)


class GenericRecordData(RecordData):
    def to_bytes(self, offset, composer):
        """ Convert to bytes

        Args:
            offset (int): offset in message
            composer (Composer): domain name composer
        """
        return self.data

    @classmethod
    def from_bytes(cls, packet, offset, rdlength, parser):
        """ Create a RecordData object from bytes

        Args:
            packet (bytes): packet
            offset (int): offset in message
            rdlength (int): length of rdata
            parser (int): domain name parser
        """
        data = packet[offset:offset+rdlength]
        return cls(data)
