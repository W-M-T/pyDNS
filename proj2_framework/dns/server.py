#!/usr/bin/env python2

""" A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""

import socket
from threading import Thread
import platform
import dns.message
import dns.resolver

class RequestHandler(Thread):
    """ A handler for requests to the DNS server """

    def __init__(self, serversocket, clientIP, packet, resolver):
        """ Initialize the handler thread """
        super().__init__()
        self.daemon = True
        self.serversocket = serversocket
        self.clientIP = clientIP
        self.msg = dns.message.from_bytes(packet)
        self.resolver = resolver
        
    def handle_request(self):#parse message en stuur reply
        pass
        
    def run(self):
        """ Run the handler thread """
        try:
            self.handle_request()
        except socket.error, e:
            print("Error handling connection: " + str(e))


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
        self.connlist = []

    def accept_request(self, s):
        packet, clientIP = s.recvfrom(2048)#2048 ok? of groter ook nodig?
        rh = RequestHandler(s, clientIP, packet, self.resolver)
        self.connlist.append(rh)
        rh.run()

    def serve(self):
        """ Start serving request """
        print("[+] - DNS Server up and running.")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        s.bind(('', self.port))

        #Zorgt ervoor dat Windows ook reageert op keyboard interrupts.
        if platform.system() == 'Windows':
            s.settimeout(1)#Deze timeout langer maken als het invloed heeft op het gedrag van de server
            while not self.done:
                try:
                    self.accept_request(s)
                except (socket.timeout):
                    pass
        else:
            while not self.done:
                self.accept_request(s)

    def shutdown(self):
        """ Shutdown the server """
        print("MAY YE FIND MANY SHUCKLES")
        self.done = True
        # TODO: shutdown socket
