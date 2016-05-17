#!/usr/bin/env python2

""" A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""

import socket
from threading import Thread


class RequestHandler(Thread):
    """ A handler for requests to the DNS server """

    def __init__(self, serversocket, clientIP, message):
        """ Initialize the handler thread """
        super().__init__()
        self.daemon = True
        self.serversocket = serversocket
        self.clientIP = clientIP
        self.message = message

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
    done = False

    def __init__(self, port, caching, ttl):
        """ Initialize the server
        
        Args:
            port (int): port that server is listening on
            caching (bool): server uses resolver with caching if true
            ttl (int): ttl for records (if > 0) of cache
        """
        self.caching = caching
        self.ttl = ttl
        self.port = port

    def serve(self):
        """ Start serving request """
        print("[+] - DNS Server up and running.")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        s.bind(('', self.port))
        
        while not self.done:
            # TODO: receive request and open handler
            message, clientIP = s.recvfrom(2048)#2048 ok? of groter ook nodig?
            rh = RequestHandler(s, clientIP, message)
            rh.run()
            

    def shutdown(self):
        """ Shutdown the server """
        self.done = True
        # TODO: shutdown socket
