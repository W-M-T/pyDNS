# Project 2 Framework

## Description

This directory contains a framework for a DNS resolver and a recursive DNS server.
The framework provides classes for manipulating DNS messages (and converting them to bytes).
The framework also contains a few stubs which you need to implement.
Most files contain pointers to the relevant sections of RFC 1034 and RFC 1035.
These are not the only relevant sections though, and you might need to read more of the RFCs.

It is probably a good idea to read RFC 1034 before proceeding.
This RFC explains an overview of DNS and introduces some of the naming which is also used in the framework.

## File structure

* proj1_sn1_sn2
    * dns
        * cache.py: Contains a cache for the resolver. You have to implement this.
        * classes.py: Enum of CLASSes and QCLASSes.
        * domainname.py: Classes for reading and writing domain names as bytes.
        * message.py: Classes for DNS messages.
        * rcodes.py: Enum of RCODEs.
        * resolver.py: Class for a DNS resolver. You have to implement this.
        * resource.py: Classes for DNS resource records.
        * server.py: Contains a DNS server. You have to implement this.
        * rtypes.py: Enum of TYPEs and QTYPEs.
        * zone.py: name space zones. You have to implement this.
    * dns_client.py: A simple DNS client, which serves as an example user of the resolver.
    * dns_server.py: Code for starting the DNS server and parsing args.
    * dns_tests.py: Tests for your resolver, cache and server. You have to implement this.

## Implementation Hints and Tips

You should start with implementing the resolver, which you need for the server.
You will need message.py, resource.py, rtypes.py, classes.py and rcodes.py.
You can ignore the code for converting from and to bytes from these files if
you want, but it might be useful (especially for debugging).

After finishing the resolver you need to implement caching and the DNS server.
You can implement these in any order that you like.
I suggest implementing the recursive part (the resolving) of your DNS server, before implementing the management of the servers zone.

Wireshark and dns_client.py are useful tools for debugging your resolver.
Wireshark and nslookup are useful tools for debugging your server.

