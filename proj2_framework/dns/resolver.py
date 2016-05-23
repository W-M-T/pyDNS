#!/usr/bin/env python2

""" DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""

import socket
import random

from dns.classes import Class
from dns.types import Type
import dns.cache
import dns.message
import dns.rcodes

class Resolver(object):
    """ DNS resolver """
    
    def __init__(self, timeout, caching, ttl, nameservers):
        """ Initialize the resolver
        
        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        if caching:
            self.cache = RecordCache.read_cache_file()
        self.ttl = ttl if ttl > 0 else 0 #Deze check is niet nodig voor de resolver gemaakt via de server, maar wel voor de resolver gemaakt door de client
        self.identifier = random.randint(0, 65535)
        self.nameservers = nameservers + Consts.ROOT_SERVERS

    def handle_query(self, query):
        if len(query.questions) == 1:
            #Verwerk de vraag juist
            pass
        else
            #Stuur geen reactie, of zoek uit watvoor error je voor een niet-ondersteunde functie terug moet geven.
            #Vraag even rond of deze feature wel/niet ondersteund moet worden. Na wat googelen lijkt het ongewoon te zijn om het te supporten, maar het staat wel in de rfc.
            pass
        

    def send_query(self, hostname, servers):
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 1
        query = dns.message.Message(header, [question])
        responses = []

        for server in servers:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            try:
                sock.sendto(query.to_bytes(), (server, 53))
                data = sock.recv(512)
                response = dns.message.Message.from_bytes(data)
                responses += response
                if self.caching:
                    for record in response.additionals + \
                            response.answers + response.authorities:
                        self.cache.add_record(record)
            except socket.timeout:
                pass

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
        timeout = 2 # the time waited for a response
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # Create and send query
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
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

	def save_cache():
            if self.caching:
                if self.cache is not None:
                    self.cache.write_cache_file()

    def gethostbyname(self, hostname):
        aliaslist = []
        ipaddrlist = []
        
        #0. Check if hostname is a valid FQDN.
        valid = is_valid_hostname(hostname)
        if valid:
            if hostname not in[valid[0], valid[0] + "."]:
                return hostname, [], []

        #1. See if the answer is in local information, and if so return it to the client.
        #TODO: check of we authorative zijn. Zo ja, geef dat ipv resultaat uit cache
        if self.caching:   		
            for alias in self.cache.lookup(hostname, Type.CNAME, Class.IN):
                aliaslist.append(alias)
            
            for address in self.cache.lookup(hostname, Type.A, Class.IN):
                ipaddrlist.append(address)

        if ipaddrlist is not []:
            return hostname, aliaslist, ipaddrlist

        #2. Find the best servers to ask.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        identifier = (self.identifier + random.randint(1,2048)) % 25535
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 1
        query = dns.message.Message(header, [question])

        #Volgens de RFC kan dit beter voor van specifieke servers langzaam naar de root servers te gaan
        stack = [ROOT_SERVER, query for ROOT_SERVER in Consts.ROOT_SERVERS]

        #3. Send them queries until one returns a response.
        while stack is not []:
            server, query = stack.pop()
            s.sendto(query.to_bytes(), (server, 53))
            try:
                data = s.recv(2048)
                response = Message.from_bytes(data)
            except:
                continue

            if response.header.ident != identifier:
                continue

            #if response.

        #4. Analyze the response, either:
        aliases = []
        for additional in response.additionals:
            if additional.type_ == Type.CNAME:
                aliases.append(additional.rdata.data)
                self.cache.add_record(additional)

        addresses = []
        for answer in response.answers:
            if answer.type_ == Type.A:
                addresses.append(answer.rdata.data)
                self.cache.add_record(answer)

        if addresses is not []:
            return hostname, aliases, addresses

        for authority in response.authorities:
            if authority.Type == Type.NS:
                if self.caching:
                    self.cache.add_record(authority)
                stack.push((authority, query))

        #a. if the response answers the question or contains a name
        #   error, cache the data as well as returning it back to
        #   the client.

        #b. if the response contains a better delegation to other
        #   servers, cache the delegation information, and go to
        #   step 2.

        #c. if the response shows a CNAME and that is not the
        #   answer itself, cache the CNAME, change the SNAME to the
        #   canonical name in the CNAME RR and go to step 1.

        #d. if the response shows a servers failure or other
        #   bizarre contents, delete the server from the SLIST and
        #   go back to step 3.
        
        return hostname, [], []
