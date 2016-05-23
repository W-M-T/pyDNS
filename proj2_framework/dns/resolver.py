#!/usr/bin/env python2

""" DNS Resolver

This module contains a class for resolving hostnames. You will have to implement
things in this module. This resolver will be both used by the DNS client and the
DNS server, but with a different list of servers.
"""

import socket
import random
import re

from dns.classes import Class
from dns.types import Type
from dns.cache import RecordCache
import dns.cache
import dns.message
import dns.rcodes
import dns.consts

class Resolver(object):
    """ DNS resolver """
    
    def __init__(self, timeout, caching, ttl, nameservers=[]):
        """ Initialize the resolver
        
        Args:
            caching (bool): caching is enabled if True
            ttl (int): ttl of cache entries (if > 0)
        """
        self.timeout = timeout
        self.caching = caching
        self.ttl = ttl if ttl > 0 else 0 #Deze check is niet nodig voor de resolver gemaakt via de server, maar wel voor de resolver gemaakt door de client
        if caching:
            self.cache = RecordCache(self.ttl)
        self.identifier = random.randint(0, 65535)
        self.nameservers = nameservers + dns.consts.ROOT_SERVERS

    def handle_query(self, query):
        if len(query.questions) == 1:
            #Verwerk de vraag juist
            pass
        else:
            #Stuur geen reactie, of zoek uit watvoor error je voor een niet-ondersteunde functie terug moet geven.
            #Vraag even rond of deze feature wel/niet ondersteund moet worden. Na wat googelen lijkt het ongewoon te zijn om het te supporten, maar het staat wel in de rfc.
            pass
        

    def send_query(self, query, servers):
        responses = []
        for server in servers:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            try:
                sock.sendto(query.to_bytes(), (server, 53))
                data = sock.recv(512)
                response = dns.message.Message.from_bytes(data)
                if response.header.ident != query.header.ident:
                    continue

                responses.append(response)
                if self.caching:
                    for record in response.additionals + \
                            response.answers + response.authorities:
                        self.cache.add_record(record)
            except socket.timeout:
                pass
        return responses

	def save_cache(self):
            if self.caching:
                if self.cache is not None:
                    self.cache.write_cache_file()

    def is_valid_hostname(self, hostname):
        valid_hostnames = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
        return re.match(valid_hostnames, hostname)

    def gethostbyname(self, hostname):
        aliaslist = []
        ipaddrlist = []
        hints = self.nameservers
        #0. Check if hostname is a valid FQDN.
        valid = self.is_valid_hostname(hostname)
        if not valid:
            return hostname, [], []

        #1. See if the answer is in local information, and if so return it to the client.
        #TODO: check of we authorative zijn. Zo ja, geef dat ipv resultaat uit cache
        if self.caching:   		
            for alias in self.cache.lookup(hostname, Type.CNAME, Class.IN):
                aliaslist.append(alias)
            
            for address in self.cache.lookup(hostname, Type.A, Class.IN):
                ipaddrlist.append(address)

        if ipaddrlist != []:
            return hostname, aliaslist, ipaddrlist

        #2. Find the best servers to ask.
        #TODO: dat doen ipv aan alle bekende sturen

        #3. Send them queries until one returns a response.
        identifier = (self.identifier + random.randint(1,2048)) % 25535
        question = dns.message.Question(hostname, Type.A, Class.IN)
        header = dns.message.Header(identifier, 0, 1, 0, 0, 0)
        header.qr = 0
        header.opcode = 0
        header.rd = 1
        query = dns.message.Message(header, [question])
        
        while hints != []:
            responses = self.send_query(query, hints)
            hints = []

            if responses is None:
                print("Not a single server responded... something is wrong.")
                return hostname, [], []

            #4. Analyze the response
            for response in responses:
                for answer in response.answers:
                    if answer.type == Type.A and (answer.name == hostname or answer.name in aliaslist):  
                        ipaddrlist.append(answers.rdata.data)
                    if answer.type == Type.CNAME and (answer.name == hostname or answer.name in aliaslist):
                        if answer.rdata.data not in aliases:
                            aliaslist.append(answer.rdata.data)

                for additional in response.additionals:
                    if additional.type == Type.CNAME and (additional.name == hostname or additional.name in aliaslist):
                        if additional.rdata.data not in aliaslist:
                            aliaslist.append(additional.rdata.data)

                if addresses != []:
                    return hostname, aliases, addresses

                for authority in response.authorities:
                    if authority.Type == Type.NS:
                        hints = [authority] + hints

        return hostname, [], []
        #, either:
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
        
        
