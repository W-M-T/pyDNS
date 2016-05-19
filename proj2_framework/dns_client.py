#!/usr/bin/env python2

""" Simple DNS client

A simple example of a client using the DNS resolver.
"""

import dns.resolver

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="DNS Client")
    parser.add_argument("hostname", help="hostname to resolve", nargs='?', type=str, default="www.nu.nl")
    parser.add_argument("-c", "--caching", action="store_true",
            help="Enable caching")
    parser.add_argument("-t", "--ttl", metavar="time", type=int, default=0, 
            help="TTL value of cached entries")
    args = parser.parse_args()
    
    # Resolve hostname
    resolver = dns.resolver.Resolver(args.caching, args.ttl)
    hostname, aliases, addresses = resolver.gethostbyname(args.hostname)
    
    # Print output
    print(hostname)
    print(aliases)
    print(addresses)
