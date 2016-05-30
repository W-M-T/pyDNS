#!/usr/bin/env python2

import argparse
import unittest
import sys
import time
from threading import Thread

import dns.resolver
import dns.resource
import dns.types
import dns.classes
import dns.server


""" Tests for your DNS resolver and server """

portnr = 5353
server = "localhost"

class TestResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, False, 1000)

    def atestNoCacheResolveExistingFQDN(self):
        h, al, ad = self.resolver.gethostbyname("gaia.cs.umass.edu")
        self.assertEqual("gaia.cs.umass.edu", h)
        self.assertEqual([], al)
        self.assertEqual(["128.119.245.12"], ad)

    def atestNoCacheResolveNotExistingFQDN(self):
        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual([], ad)


class TestResolverCache(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, True, 10)

    def atestResolveInvalidCachedFQDN(self):
        shuckleRecord = dns.resource.ResourceRecord("s.h.u.c.k.l.e",\
                dns.types.Type.A, dns.classes.Class.IN,\
                int(time.time() + 5), dns.resource.RecordData("42.42.42.42"))
        self.resolver.cache.add_record(shuckleRecord)

        #Server checks if FQDN is valid before processing, therefore
        #we use a FQDN that could be valid, but is not.

        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual(["42.42.42.42"], ad)

    def atestResolveExpiredInvalidCachedFQDN(self):
        shuckleRecord = dns.resource.ResourceRecord("s.h.u.c.k.l.e",\
                dns.types.Type.A, dns.classes.Class.IN,\
                int(time.time() + 5), dns.resource.RecordData("42.42.42.42"))
        self.resolver.cache.add_record(shuckleRecord)

        time.sleep(5+1)

        h, al, ad = self.resolver.gethostbyname("s.h.u.c.k.l.e")
        self.assertEqual("s.h.u.c.k.l.e", h)
        self.assertEqual([], al)
        self.assertEqual([], ad)

class TestServer(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, False, 10)
        self.offline_resolver = dns.resolver.Resolver(5, False, 10, ["localhost"], False)
        #self.server = dns.server.Server(53, False, 5).serve()

    def atestSolveFQDNDirectAuthority(self):
        h1, al1, ad1 = self.resolver.gethostbyname("shuckle.ru.nl")
        h2, al2, ad2 = self.offline_resolver.gethostbyname("ru.nl")

        self.assertEqual(al1, al2)
        self.assertEqual(ad1, ad2)

    def testSolveFQDNNoDirectAuthority(self):
        h1, al1, ad1 = self.resolver.gethostbyname("cs.ru.nl")
        h2, al2, ad2 = self.offline_resolver.gethostbyname("cs.ru.nl")

        self.assertEqual(h1, h2)
        self.assertEqual(al1, al2)
        self.assertEqual(ad1, ad2)

    def testSolveFQDNNotInZone(self):
        h, al, ad = self.offline_resolver.gethostbyname("hestia.dance")

        self.assertEqual("hestia.dance", h)
        self.assertEqual([], al)
        self.assertEqual(["162.246.59.52"], ad)

    def atestParallelRequest(self):
    	helper1 = ThreadHelper(self.offline_resolver, "hestia.dance")
    	helper2 = ThreadHelper(self.offline_resolver, "gaia.cs.umass.edu")
    	t1 = Thread(target=helper1.run)
    	t2 = Thread(target=helper2.run)
    	t1.daemon = True
    	t2.daemon = True
    	t1.start()
    	t2.start()
    	t1.join()
    	t2.join()

    	self.assertEqual("hestia.dance", helper1.h)
        self.assertEqual([], helper1.al)
        self.assertEqual(["162.246.59.52"], helper1.ad)

        self.assertEqual("gaia.cs.umass.edu", helper2.h)
        self.assertEqual([], helper2.al)
        self.assertEqual(["128.119.245.12"], helper2.ad)
        

class ThreadHelper(Thread):

    def __init__(self, resolver, hname):
        super(ThreadHelper, self).__init__()
        self.resolver = resolver
        self.hname = hname
        self.h = []
        self.al = []
        self.ad = []

    def run(self):
    	self.h, self.al, self.ad = self.resolver.gethostbyname(self.hname)
        


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
