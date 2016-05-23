#!/usr/bin/env python2

import argparse
import unittest
import sys

import dns.resolver


""" Tests for your DNS resolver and server """

portnr = 5353
server = "localhost"

class TestResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = dns.resolver.Resolver(5, True, 1000)

    def testFQDN(self):
        h, al, ad = self.resolver.gethostbyname("gaia.cs.umass.edu")
        self.assertEqual("gaia.cs.umass.edu", h)
        self.assertEqual([], al)
        self.assertEqual(["128.119.245.12"], ad)


class TestResolverCache(unittest.TestCase):
    pass


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
