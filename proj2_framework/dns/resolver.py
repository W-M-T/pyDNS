#!/usr/bin/env python2

""" DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""

import socket

from dns.cache import RecordCache
from dns.classes import Class
from dns.message import Message, Header, Question
from dns.rcodes import RCode
from dns.types import Type

class Resolver(object):
    """ DNS resolver """
    
    def __init__(self, caching, ttl):
        """ Initialize the resolver
        
        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.caching = caching
        self.ttl = ttl

    def gethostbyname(self, hostname):
        """ Translate a host name to IPv4 address.

        Currently this method contains an example. You will have to replace
        this example with example with the algorithm described in section
        5.3.3 in RFC 1034.

        Args:
            hostname (str): the hostname to resolve

        Returns:
            (str, [str], [str]): (hostname, aliaslist, ipaddrlist)
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # Create and send query
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(9001, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 1
        query = dns.message.Message(header, [question])
        sock.sendto(query.to_bytes(), ("8.8.8.8", 53))

        # Receive response
        data = sock.recv(512)
        response = dns.message.Message.from_bytes(data)

        # Get data
        aliases = []
        for additional in response.additionals:
            if additional.type_ == Type.CNAME:
                aliases.append(additional.rdata.data)
        addresses = []
        for answer in response.answers:
            if answer.type_ == Type.A:
                addresses.append(answer.rdata.data)

        return hostname, aliases, addresses
