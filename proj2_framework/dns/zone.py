#!/usr/bin/env python2
import re

""" Zones of domain name space 

See section 6.1.2 of RFC 1035 and section 4.2 of RFC 1034.
Instead of tree structures we simply use dictionaries from domain names to
zones or record sets.

These classes are merely a suggestion, feel free to use something else.
"""

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

    #Kan mooier met een dict, maar het werkt.
    #Als je zin hebt om het te verbeteren, ga je gang.
    def time_to_seconds_helper(self, timestring):
        if (timestring[-1] in ['s', 'S']):
            return int(timestring[:-1])
        if (timestring[-1] in ['m', 'M']):
            return 60 * int(timestring[:-1])
        if (timestring[-1] in ['h', 'H']):
            return 3600 * int(timestring[:-1])
        if (timestring[-1] in ['w', 'W']):
            return 86400 * int(timestring[:-1])
        if (timestring[-1] in ['d', 'D']):
            return 604800 * int(timestring[:-1])
        return 0

    def time_to_seconds(self, timestring):
        return sum(map(time_to_seconds_helper, re.findall(re.compile("\d+\w"), timestring)))

    def parse_and_load(self, content):
        content = re.sub(re.compile(";.*?\n"), "\n", content) #Remove comments
        content = re.sub(re.compile("\n\n*\n") , "\n", content) #Remove whitespaces
        content = re.sub(re.compile("  * ") , " ", content) #Remove multiple spaces between words
        content = re.sub(re.compile("\t\t*\t") , " ", content) #Remove tabs between words
        content = re.sub(re.compile("\n *") , "\n", content) #Remove spaces at start of line
        content = re.sub(re.compile("\n\t*") , "\n", content) #Remove tabs at start of line
        content = re.compile(r'\(.*?\)', re.DOTALL)\
        .sub(lambda x: x.group().replace('\n', ''), content) #Remove newlines between ()

        ttl = None
        origin = None

        for line in content:
            if line[:4] == "$TTL":
                ttl = time_to_seconds(strip(line[4:]))
            elif line[:7] == "$ORIGIN":
                origin = strip(line[7:])
            elif "IN SOA" in line:
                pass

