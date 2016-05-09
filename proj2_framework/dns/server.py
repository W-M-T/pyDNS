#!/usr/bin/env python2

""" A recursive DNS server

This module provides a recursive DNS server. You will have to implement this
server using the algorithm described in section 4.3.2 of RFC 1034.
"""

import socket
from threading import Thread


class RequestHandler(Thread):
    """ A handler for requests to the DNS server """

    def __init__(self):
        """ Initialize the handler thread """
        super().__init__()
        self.daemon = True
        
    def run(self):
        """ Run the handler thread """
        # TODO: Handle DNS request
        pass


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
        self.ttl = ttl
        self.port = port
        # TODO: create socket

    def serve(self):
        """ Start serving request """
        # TODO: start listening
        while not self.done:
            # TODO: receive request and open handler
            pass

    def shutdown(self):
        """ Shutdown the server """
        self.done = True
        # TODO: shutdown socket
