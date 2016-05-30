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
        self.nameservers = nameservers
        if use_rs:
            self.nameservers += dns.consts.ROOT_SERVERS


    def is_valid_hostname(self, hostname):
        """ Check if hostname could be a valid hostname

        Args:
            hostname (str): the hostname that is to be checked

        Returns:
            boolean indiciting if hostname could be valid
        """
        valid_hostnames = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        return re.match(valid_hostnames, hostname)


    def save_cache(self):
        """ Save the cache if appropriate """
        if self.caching:
            if self.cache is not None:
                self.cache.write_cache_file()


    def ask_server(self, query, server):
        """ Send query to a server

        Args: 
            query (Message): the query that is to be sent
            server (str): IP address of the server that the query must be sent to
        
        Returns:
            responses ([Message]): the responses received converted to Messages
        """
        response = None
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            sock.sendto(query.to_bytes(), (server, 53))
            data = sock.recv(1024)
            response = dns.message.Message.from_bytes(data)
            if response.header.ident != query.header.ident:
                return None
            
            if self.caching:
                for record in response.additionals + response.answers + response.authorities:
                    if record.type == Type.A or record.type == Type.CNAME:
                        record.ttl = self.ttl
                        record.timestamp = int(time.time())
                        self.cache.add_record(record)
                    
        except socket.timeout:
            pass
        
        return response


    def gethostbyname(self, hostname):
        """ Resolve hostname to an IP address

        Args:
            hostname (str): the FQDN that we want to resolve

        Returns:
            hostname (str): the FQDN that we want to resolve,
            aliaslist ([str]): list of aliases of the hostname,
            ipaddrlist ([str]): list of IP addresses of the hostname 

        """

        #Check if the hostname is valid
        valid = self.is_valid_hostname(hostname)
        if not valid:
            return hostname, [], []

        #Check if the information is in the cache
        if self.caching:   		
            for alias in self.cache.lookup(hostname, Type.CNAME, Class.IN):
                aliaslist.append(alias.rdata.data)
            
            for address in self.cache.lookup(hostname, Type.A, Class.IN):
                ipaddrlist.append(address.rdata.data)

            if ipaddrlist:
                return hostname, aliaslist, ipaddrlist

        #Do the recursive algorithm
        aliaslist = []
        ipaddrlist = []
        hints = self.nameservers
        
        while hints:
            #Get the server to ask
            hint = hints[0]
            hints = hints[1:]

            #Build the query to send to that server
            identifier = randint(0, 65535)
            
            question = dns.message.Question(hostname, Type.A, Class.IN)
            header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
            header.qr = 0
            header.opcode = 0
            header.rd = 0
            query = dns.message.Message(header, [question])

            #Try to get a response
            response = self.ask_server(query, hint)

            if response == None:#We didn't get a response for this server, so check the next one
                continue

            #Analyze the response
            for answers in response.answers + response.additionals:#First get the aliases
                if answer.type_ == Type.CNAME and answer.rdata.data not in aliases:
                    aliaslist.append(answer.rdata.data)

            for answers in response.answers:#Then try to get an address
                if answer.type_ == Type.A and (answer.name == hostname or answer.name in aliaslist):  
                    ipaddrlist.append(answer.rdata.data)
                
            if ipaddrlist != []:
                print("We found an address using the recursive search!")
                return hostname, aliaslist, ipaddrlist

            else:
                for nameserver in response.authorities:
                    if nameserver.type_ == Type.NS:#Do a lookup for that ns?
                        print(nameserver.rdata.data)
                        if self.caching:
                            self.cache.add_record(nameserver)
                        hints = [nameserver.rdata.data] + hints

        print("Recursive search for " + hostname + " was a total failure")
        return hostname, [], []
