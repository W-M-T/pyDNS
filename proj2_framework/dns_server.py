#!/usr/bin/env python2

""" DNS server

This script contains the code for starting a DNS server.
"""

import dns.server
import time

if __name__ == "__main__":
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="DNS Server")
    parser.add_argument("-c", "--caching", action="store_true",
            help="Enable caching")
    parser.add_argument("-t", "--ttl", metavar="time", type=int, default=0, 
            help="TTL value of cached entries (if > 0)")
    parser.add_argument("-p", "--port", type=int, default=5353,
            help="Port which server listens on")
    args = parser.parse_args()

    # Start server
    server = dns.server.Server(args.port, args.caching, args.ttl)
    try:
        server.serve()
        print("[*] - Server ended.")
    except KeyboardInterrupt:
        print("\n[*] - Trying to shut down.")
        server.shutdown()
        print("[*] - Shutting down.\n")
        time.sleep(1)
