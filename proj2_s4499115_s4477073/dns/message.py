#!/usr/bin/env python3

""" DNS messages

This module contains classes for DNS messages, their header section and
question fields. See section 4 of RFC 1035 for more info.
"""

import socket
import struct

from dns.classes import Class
from dns.domainname import Parser, Composer
from dns.resource import ResourceRecord
from dns.rtypes import Type


class Message(object):
    """ DNS message """

    def __init__(self, header, questions=[], answers=[], authorities=[], additionals=[]):
        """ Create a new DNS message
        
        Args:
            header (Header): the header section
            questions ([Question]): the question section
            answers ([ResourceRecord]): the answer section
            authorities ([ResourceRecord]): the authority section
            additionals ([ResourceRecord]): the additional section
        """
        self.header = header
        self.questions = questions
        self.answers = answers
        self.authorities = authorities
        self.additionals = additionals

    @property
    def resources(self):
        """ Getter for all resource records """
        return self.answers + self.authorities + self.additionals

    def to_bytes(self):
        """ Convert Message to bytes """
        composer = Composer()

        # Add header
        result = self.header.to_bytes()

        # Add questions
        for question in self.questions:
            offset = len(result)
            result += question.to_bytes(offset, composer)

        # Add answers
        for answer in self.answers:
            offset = len(result)
            result += answer.to_bytes(offset, composer)

        # Add authorities
        for authority in self.authorities:
            offset = len(result)
            result += authority.to_bytes(offset, composer)

        # Add additionals
        for additional in self.additionals:
            offset = len(result)
            result += additional.to_bytes(offset, composer)

        return result

    @classmethod
    def from_bytes(cls, packet):
        """ Create Message from bytes

        Args:
            packet (bytes): byte representation of the message
        """
        parser = Parser()

        # Parse header
        header, offset = Header.from_bytes(packet), 12

        # Parse questions
        questions = []
        for _ in range(header.qd_count):
            question, offset = Question.from_bytes(packet, offset, parser)
            questions.append(question)

        # Parse answers
        answers = []
        for _ in range(header.an_count):
            answer, offset = ResourceRecord.from_bytes(packet, offset, parser)
            answers.append(answer)

        # Parse authorities
        authorities = []
        for _ in range(header.ns_count):
            auth, offset = ResourceRecord.from_bytes(packet, offset, parser)
            authorities.append(auth)

        # Parse additionals
        additionals = []
        for _ in range(header.ar_count):
            add, offset = ResourceRecord.from_bytes(packet, offset, parser)
            additionals.append(add)

        return cls(header, questions, answers, authorities, additionals)


class Header(object):
    """ The header section of a DNS message
    
    Contains a number of properties which are accessible as normal member
    variables.

    See section 4.1.1 of RFC 1035 for their meaning.
    """
    
    def __init__(self, ident, flags, qd_count, an_count, ns_count, ar_count):
        """ Create a new Header object

        Args:
            ident (int): identifier
            qd_count (int): number of entries in question section
            an_count (int): number of entries in answer section
            ns_count (int): number of entries in authority section
            ar_count (int): number of entries in additional section
        """
        self.ident = ident
        self._flags = flags
        self.qd_count = qd_count
        self.an_count = an_count
        self.ns_count = ns_count
        self.ar_count = ar_count

    def to_bytes(self):
        """ Convert header to bytes """
        return struct.pack("!6H", 
                self.ident,
                self._flags, 
                self.qd_count, 
                self.an_count, 
                self.ns_count, 
                self.ar_count)

    @classmethod
    def from_bytes(cls, packet):
        """ Convert Header from bytes """
        if len(packet) < 12:
            raise ShortHeader
        return cls(*struct.unpack_from("!6H", packet))
   
    @property
    def flags(self):
        return self._flags
    @flags.setter
    def flags(self, value):
        if value >= (1 << 16):
            raise ValueError("value too big for flags")
        self._flags = value

    #Is dit een query? Dan 0. Is dit een response? Dan 1.
    @property
    def qr(self):
        return self._flags & (1 << 15)
    @qr.setter
    def qr(self, value):
        if value:
            self._flags |= (1 << 15)
        else:
            self._flags &= ~(1 << 15)

    @property
    def opcode(self):
        return (self._flags & (((1 << 4) - 1) << 11)) >> 11
    @opcode.setter
    def opcode(self, value):
        if value > 0b1111:
            raise ValueError("invalid opcode")
        self._flags &= ~(((1 << 4) - 1) << 11)
        self._flags |= value << 11

    @property
    def aa(self):
        return self._flags & (1 << 10)
    @aa.setter
    def aa(self, value):
        if value:
            self._flags |= (1 << 10)
        else:
            self._flags &= ~(1 << 10)

    @property
    def tc(self):
        return self._flags & (1 << 9)
    @tc.setter
    def tc(self, value):
        if value:
            self._flags |= (1 << 9)
        else:
            self._flags &= ~(1 << 9)

    @property
    def rd(self):
        return self._flags & (1 << 8)
    @rd.setter
    def rd(self, value):
        if value:
            self._flags |= (1 << 8)
        else:
            self._flags &= ~(1 << 8)

    @property
    def ra(self):
        return self._flags & (1 << 7)
    @ra.setter
    def ra(self, value):
        if value:
            self._flags |= (1 << 7)
        else:
            self._flags &= ~(1 << 7)

    @property
    def z(self):
        return (self._flags & (((1 << 3) - 1) << 4) >> 4)
    @z.setter
    def z(self, value):
        if value:
            raise ValueError("non-zero zero flag")

    @property
    def rcode(self):
        return self._flags & ((1 << 4) - 1)
    @rcode.setter
    def rcode(self, value):
        if value > 0b1111:
            raise ValueError("invalid return code")
        self._flags &= ~((1 << 4) - 1)
        self._flags |= value


class Question(object):
    """ An entry in the question section.

    See section 4.1.2 of RFC 1035 for more info.
    """

    def __init__(self, qname, qtype, qclass):
        """ Create a new entry in the question section 
        
        Args:
            qname (str): QNAME
            qtype (Type): QTYPE
            qclass (Class): QCLASS
        """
        self.qname = qname
        self.qtype = qtype
        self.qclass = qclass

    def to_bytes(self, offset, composer):
        """ Convert Question to bytes """
        bqname = composer.to_bytes(offset, [self.qname])
        bqtype = struct.pack("!H", self.qtype)
        bqclass = struct.pack("!H", self.qclass)
        return bqname + bqtype + bqclass

    @classmethod
    def from_bytes(cls, packet, offset, parser):
        """ Convert Question from bytes """
        qnames, offset = parser.from_bytes(packet, offset, 1)
        qname = qnames[0]
        qtype, qclass = struct.unpack_from("!2H", packet, offset)
        return cls(qname, qtype, qclass), offset + 4
