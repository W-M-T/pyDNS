#!/usr/bin/env python2

import argparse
import unittest
import sys
import time

import dns.resolver
import dns.resource
import dns.types
import dns.classes


""" Tests for your DNS resolver and server """

portnr = 5353
server = "localhost"

class TestResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, False, 1000)

    def testNoCacheResolveExistingFQDN(self):
        h, al, ad = self.resolver.gethostbyname("gaia.cs.umass.edu")
        self.assertEqual("gaia.cs.umass.edu", h)
        self.assertEqual([], al)
        self.assertEqual(["128.119.245.12"], ad)

    def testNoCacheResolveNotExistingFQDN(self):
        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual([], ad)


class TestResolverCache(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, True, 10)

    def testResolveInvalidCachedFQDN(self):
        shuckleRecord = dns.resource.ResourceRecord("s.h.u.c.k.l.e",\
                dns.types.Type.A, dns.classes.Class.IN,\
                5, dns.resource.RecordData("42.42.42.42"))
        self.resolver.cache.add_record(shuckleRecord)

        #Server checks if FQDN is valid before processing, therefore
        #we use a FQDN that could be valid, but is not.

        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual(["42.42.42.42"], ad)

    def testResolveExpiredInvalidCachedFQDN(self):
        #TODO: check of TTL relatieve tijd is of absolute tijd
        shuckleRecord = dns.resource.ResourceRecord("s.h.u.c.k.l.e",\
                dns.types.Type.A, dns.classes.Class.IN,\
                5, dns.resource.RecordData("42.42.42.42"))
        self.resolver.cache.add_record(shuckleRecord)

        time.sleep(5+1)

        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual([], ad)




class TestServer(unittest.TestCase):
    pass


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="HTTP Tests")
    parser.add_argument("-s", "--server", type=str, default="localhost")
    parser.add_argument("-p", "--port", type=int, default=5001)
    args, extra = parser.parse_known_args()
    portnr = args.port
    server = args.server
    
    # Pass the extra arguments to unittest
    sys.argv[1:] = extra

    # Start test suite
    unittest.main()
