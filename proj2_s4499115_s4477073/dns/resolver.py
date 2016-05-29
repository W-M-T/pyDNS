#!/usr/bin/env python2

""" DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""

import socket
import random
import re
import time

from dns.classes import Class
from dns.types import Type
from dns.cache import RecordCache
import dns.cache
import dns.message
import dns.rcodes
import dns.consts

class Resolver(object):
    """ DNS resolver """
    
    def __init__(self, timeout, caching, ttl, nameservers=[], use_rs=True):
        """ Initialize the resolver
        
        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        self.ttl = ttl if ttl > 0 else 0 #Deze check is niet nodig voor de resolver gemaakt via de server, maar wel voor de resolver gemaakt door de client
        if caching:
            self.cache = RecordCache()
        self.identifier = random.randint(0, 65535)
        self.nameservers = nameservers
        if use_rs:
            self.nameservers += dns.consts.ROOT_SERVERS
        
    def send_query(self, query, servers):
        """ Send query to each server in servers

        Args: 
            query (Message): the query that is to be send
            servers ([str]): IP addresses of the server that the query must be sent to
        
        Returns:
            responses ([Message]): the responses received converted to Messages
        """
        responses = []
        for server in servers:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            try:
                sock.sendto(query.to_bytes(), (server, 53))
                data = sock.recv(1024)
                response = dns.message.Message.from_bytes(data)
                if response.header.ident != query.header.ident:
                    continue

                responses.append(response)
                if self.caching:
                    for record in response.additionals + response.answers + response.authorities:
                        record.ttl = self.ttl
                        record.timestamp = int(time.time())
                        self.cache.add_record(record)
            except socket.timeout:
                pass
        return responses

    def save_cache(self):
        """ Save the cache if appropriate """
        if self.caching:
            if self.cache is not None:
                self.cache.write_cache_file()

    def is_valid_hostname(self, hostname):
        """ Check if hostname could be a valid hostname

        Args:
            hostname (str): the hostname that is to be checked

        Returns:
            boolean indiciting if hostname could be valid
        """
        valid_hostnames = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        return re.match(valid_hostnames, hostname)

    def gethostbyname(self, hostname):
        """ Resolve hostname to an IP address

        Args:
            hostname (str): the FQDN that we want to resolve

        Returns:
            hostname (str): the FQDN that we want to resolve,
            aliaslist ([str]): list of aliases of the hostname,
            ipaddrlist ([str]): list of IP addresses of the hostname 

        """
        aliaslist = []
        ipaddrlist = []
        hints = self.nameservers

        valid = self.is_valid_hostname(hostname)
        if not valid:
            return hostname, [], []

        if self.caching:   		
            for alias in self.cache.lookup(hostname, Type.CNAME, Class.IN):
                aliaslist.append(alias.rdata.data)
            
            for address in self.cache.lookup(hostname, Type.A, Class.IN):
                ipaddrlist.append(address.rdata.data)

        if ipaddrlist:
            return hostname, aliaslist, ipaddrlist

        #Send them queries until one returns a response.
        identifier = (self.identifier + random.randint(1,2048)) % 25535
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 1
        query = dns.message.Message(header, [question])
        
        while hints:
            responses = self.send_query(query, [hints[0]])

            hints = []
            while responses is None and hints:
            	hints = hints[1:]
            	responses = self.send_query(query, [hints[0]])

            if responses is None:
                return hostname, [], []

            #Analyze the response
            for response in responses:
                for answer in response.answers:
                    if answer.type_ == Type.A and (answer.name == hostname or answer.name in aliaslist):  
                        ipaddrlist.append(answer.rdata.data)
                    if answer.type_ == Type.CNAME and (answer.name == hostname or answer.name in aliaslist):
                        if answer.rdata.data not in aliases:
                            aliaslist.append(answer.rdata.data)

                for additional in response.additionals:
                    if additional.type_ == Type.CNAME and (additional.name == hostname or additional.name in aliaslist):
                        if additional.rdata.data not in aliaslist:
                            aliaslist.append(additional.rdata.data)

                if ipaddrlist != []:
                    return hostname, aliaslist, ipaddrlist

                for authority in response.authorities:
                    if authority.type_ == Type.NS:
                        hints = [authority.rdata.data] + hints

        return hostname, [], []
