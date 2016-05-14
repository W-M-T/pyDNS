#!/usr/bin/env python2
import re

""" Zones of domain name space 

See section 6.1.2 of RFC 1035 and section 4.2 of RFC 1034.
Instead of tree structures we simply use dictionaries from domain names to
zones or record sets.

These classes are merely a suggestion, feel free to use something else.
"""

#content = open('test.txt').read()
#content = re.sub(re.compile(";.*?\n"), "\n", content)
#content = re.sub(re.compile("\n\n*\n") , "\n", content)
#Remove indentation
#content = re.sub(re.compile("  * ") , " ", content) #Remove multiple spaces between words
#content = re.sub(re.compile("\t\t*\t") , " ", content) #Remove tabs between words
#content = re.sub(re.compile("\n *") , "\n", content) #Remove spaces at start of line
#content = re.sub(re.compile("\n\t*") , "\n", content) #Remove tabs at start of line
#print(content)
class Catalog(object):
    """ A catalog of zones """

    def __init__(self):
        """ Initialize the catalog """
        self.zones = {}

    def add_zone(self, name, zone):
        """ Add a new zone to the catalog
        
        Args:
            name (str): root domain name
            zone (Zone): zone
        """
        self.zones[name] = zone


class Zone(object):
    """ A zone in the domain name space """

    def __init__(self):
        """ Initialize the Zone """
        self.records = {}

    def add_node(self, name, record_set):
        """ Add a record set to the zone

        Args:
            name (str): domain name
            record_set ([ResourceRecord]): resource records
        """
        self.records[name] = record_set

    def read_master_file(self, filename):
        """ Read the zone from a master file

        See section 5 of RFC 1035.

        Args:
            filename (str): the filename of the master file
        """
        try:
            with open(filename) as infile:
                data = infile.read()
                self.parse_and_load(data)
        except IOError, e:
            print("An error has occured while reading the zone from file: " \
                + str(filename) + " - " + str(e))

    def parse_and_load(self, content):
        #Remove comments
        content = re.sub(re.compile(";.*?\n"), "\n", content)
        #Remove whitespaces
        content = re.sub(re.compile("\n\n*\n") , "\n", content)
        #Remove indentation
        content = re.sub(re.compile("  * ") , " ", content) #Remove multiple spaces between words
        content = re.sub(re.compile("\t\t*\t") , " ", content) #Remove tabs between words
        content = re.sub(re.compile("\n *") , "\n", content) #Remove spaces at start of line
        content = re.sub(re.compile("\n\t*") , "\n", content) #Remove tabs at start of line

