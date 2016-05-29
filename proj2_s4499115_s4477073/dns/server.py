#!/usr/bin/env python2

""" A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""

import socket
from threading import Thread, Lock
import platform
import dns.message
import dns.resolver
import dns.zone

from dns.resource import ResourceRecord, ARecordData, CNAMERecordData
from dns.classes import Class
from dns.types import Type


lock = Lock()


class RequestHandler(Thread):
    """ A handler for requests to the DNS server """

    def __init__(self, serversocket, clientIP, ttl, message, resolver, catalog):
        """ Initialize the handler thread """
        super(RequestHandler, self).__init__()
        self.daemon = True
        self.socket = serversocket
        self.clientIP = clientIP
        self.ttl = ttl
        self.message = message
        self.resolver = resolver
        self.catalog = catalog

    def check_zone(self, hname):
        """ Checks the catalog for entries regarding given hname

        Args:
            hname (str): the FQDN of the host we want to look up

        Returns:
            hname (str): the FQDN of the host we want to look up,
            answer ([ResourceRecord]): the records that directly give an IP address,
            authority ([ResourceRecord]): the records that tell about the nameservers that "know more",
            A boolean that tells if we found something
        """

        hparts = hname.split('.')

        zone_match = None
        best_rdn_parts = []

        #Check if hname is a subdomain for the root domain name
        for rdn in self.catalog.zones:
            zone = self.catalog.zones[rdn]
            rdn_parts = rdn.split('.')
            if all(l == r for (l, r) in zip(reversed(hparts), reversed(rdn_parts))) and len(hparts) <= len(rdn_parts):
                zone_match = zone
                best_rdn_parts = rdn_parts
                
        
        if zone_match == None:
            return [], [], False

        #Find the answers
        authority = []
        answer = []

        for i in range(len(hparts)):
            subaddress = ".".join(hparts[i:])
            print(subaddress)
            
            for fqdn, record in zone_match.records.iteritems():
                
                if fqdn == subaddress and record.type != Type.NS:
                    if self.message.questions[0].qtype == record.type:
                        answer.append(record)
                        
                    elif self.message.questions[0].qtype != Type.CNAME and record.type == Type.CNAME:
                        answer.append(record)
                        #Find the info for this new cname if you have it
                        extra_answer, extra_authority, extra_found = self.check_zone(hname)
                        answer = answer + extra_answer
                        authority = authority + extra_authority
                        
                elif fqdn == subaddress and record.type == Type.NS:
                    authority.append(record)

        return (list(set(answer)), list(set(authority)), (answer != [] or authority != []))



    def handle_request(self):
        """ Attempts to answer the received query """

        print("[*] - Handling request.")
        if len(self.message.questions) != 1:
            print("[-] - Invalid request.")#Hier bestaat een statuscode voor toch?
            return
        hname = self.message.questions[0].qname
        ident = self.message.header.ident
        answer, authority, found = self.check_zone(hname)
        
        if found:
            header = dns.message.Header(ident, 0, 1, len(answer), len(authority), 0)
            header.rd = 1 if self.message.header.rd == 256 else 0
            header.ra = 1
            header.aa = 1
            header.opcode = 0
            header.qr = 1

            sendResponse(dns.message.Message(header, self.message.questions, answer, authority))

        elif self.message.header.rd == 256:
            h, al, ad = self.resolver.gethostbyname(hname)
            if ad:
                header = dns.message.Header(ident, 0, 1, len(answer), len(authority), 0)
                header.rd = 1 if self.message.header.rd == 256 else 0
                header.ra = 1
                header.opcode = 0
                header.qr = 1

                aliases = [ResourceRecord(h, Type.CNAME, Class.IN, self.ttl, CNAMERecordData(alias)) for alias in al]
                addresses = [ResourceRecord(h, Type.CNAME, Class.IN, self.ttl, ARecordData(address)) for address in ad]

                self.sendResponse(dns.message.Message(header, self.message.questions, aliases + addresses))

        #Nog een error response sturen anders?
        
            

    def sendResponse(response):
        with lock:
            print("[+] - Sending response.")
            self.socket.sendto(response.to_bytes(), self.clientIP)

    def run(self):
        """ Run the handler thread """
        try:
            self.handle_request()
        except socket.error, e:
            print("[-] - Error handling request: " + str(e))


class Server(object):
    """ A recursive DNS server """

    def __init__(self, port, caching, ttl):
        """ Initialize the server
        
        Args:
            port (int): port that server is listening on
            caching (bool): server uses resolver with caching if true
            ttl (int): ttl for records (if > 0) of cache
        """
        self.caching = caching
        self.ttl = ttl if ttl > 0 else 0
        self.port = port
        self.done = False
        self.resolver = dns.resolver.Resolver(5, self.caching, self.ttl)

        self.zone = dns.zone.Zone()
        self.zone.read_master_file()

        self.catalog = dns.zone.Catalog()
        self.catalog.add_zone("ru.nl", self.zone)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))

    def serve(self):
        """ Start serving request """
        
        print("[+] - DNS Server up and running.")
        
        while not self.done:
            data, addr = self.socket.recvfrom(1024)

            try:
                message = dns.message.Message.from_bytes(data)
            except:
                print("[-] - Received invalid data.")
                continue

            rh = RequestHandler(self.socket, addr, self.ttl, message, self.resolver, self.catalog)
            rh.start()

    def shutdown(self):
        """ Shutdown the server """
        print("[*] - Shutting down.")
        self.done = True
        self.socket.close()
        self.resolver.save_cache()
        print("[+] - Shut down complete. May your framerates be high and our temperatures low.")
