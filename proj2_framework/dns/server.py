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

lock = Lock()


class RequestHandler(Thread):
    """ A handler for requests to the DNS server """

    def __init__(self, serversocket, clientIP, message, resolver, catalog):
        """ Initialize the handler thread """
        super().__init__()
        self.daemon = True
        self.serversocket = serversocket
        self.clientIP = clientIP
        self.message = message
        self.resolver = resolver
        self.catalog = catalog

        
    def handle_request(self):
        if len(self.message.questions) != 1:
            return

        hname = self.message.questions[0].qname
        ident = self.message.header.ident
        (hostname, answer, authority, found) = check_zone(hname)

        response = None

        if found:
            header = dns.message.Header(ident, 0, 1, len(answer), len(authority), 0)
            header.rd = 1
            header.ra = 1
            header.aa = 1
            header.opcode = 0
            header.qr = 1

            response = Message(header, self.message.questions, answer, authority)

        else:
            if self.message.header.rq == 256:
                (h, al, ad) = self.resolver.gethostbyname(hname)
                if ad:
                    header = dns.message.Header(ident, 0, 1, len(answer), len(authority), 0)
                    header.rd = 1
                    header.ra = 1
                    header.opcode = 0
                    header.qr = 1

                    aliases = [ResourceRecord(hostname, Type.CNAME, Class.IN, self.ttl, CNAMERecordData(alias)) for alias in al]
                    addresses = [ResourceRecord(hostname, Type.CNAME, CLass.IN, self.ttl, ARecordData(address)) for address in ad]

                    response = Message(header, self.message.questions, aliases + addresses)
        
        with lock:
            self.socket.sendto(respone.to_bytes(), self.clientIP)

    def run(self):
        """ Run the handler thread """
        try:
            self.handle_request()
        except socket.error, e:
            print("[-] - Error handling connection: " + str(e))


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
        self.resolver = dns.resolver.Resolver(self.caching, self.ttl)

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
                message = Message.from_bytes(data)
            except:
                print("[-] - Received invalid data.")
                continue

            rh = RequestHandler(self.socket, addr, message, self.resolver)
            rh.start()

    def shutdown(self):
        """ Shutdown the server """
        print("MAY YE FIND MANY SHUCKLES")
        self.done = True
        self.socket.close()
