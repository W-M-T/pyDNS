#!/usr/bin/env python2
import re
import dns.zone
import dns.consts as Consts
import dns.classes
import dns.resource

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

    def read_master_file(self, filename=Consts.ZONE_FILE):
        """ Read the zone from a master file

        See section 5 of RFC 1035.

        Args:
            filename (str): the filename of the master file
        """
        try:
            with open(filename) as infile:
                data = infile.read()
                return self.load_and_parse(data)
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
        try:
            if timestring == int(timestring):
                return int(timestring)
            else:
                return 0
        except:
            return 0

    def time_to_seconds(self, timestring):
        return sum(map(self.time_to_seconds_helper, re.findall(re.compile("\d+\w"), timestring)))

    def load_and_parse(self, content):
        content = re.sub(re.compile(";.*?\n"), "\n", content) #Remove comments
        content = re.sub(re.compile("\n\n*\n") , "\n", content) #Remove whitespaces
        content = re.sub(re.compile("  * ") , " ", content) #Remove multiple spaces between words
        content = re.sub(re.compile("\t\t*\t") , " ", content) #Remove tabs between words
        content = re.sub(re.compile("\n *") , "\n", content) #Remove spaces at start of line
        content = re.sub(re.compile("\n\t*") , "\n", content) #Remove tabs at start of line
        content = re.compile(r'\(.*?\)', re.DOTALL)\
        .sub(lambda x: x.group().replace('\n', ''), content) #Remove newlines between ()
        content = re.sub(re.compile("\t+") , " ", content) #Remove tabs between words

        default_ttl = None
        origin = None

        recordSet = []

        for line in content.split('\n'):
            if line[:4] == "$TTL":
                prev_ttl = self.time_to_seconds(line[4:].strip())
            elif line[:7] == "$ORIGIN":
                origin = line[7:].strip()
            elif "SOA" not in line:
                parts = line.split(' ')
                rr_name = parts[0]
                
                rr_ttl = self.time_to_seconds(parts[1])
                offset = int(rr_ttl == 0)
                if offset:
                    rr_ttl = prev_ttl

                rr_class = dns.classes.Class.from_string(parts[1+offset])
                rr_type = parts[2+offset]
                rr_data = dns.resource.RecordData.create(rr_type, parts[3+offset].rstrip('.'))
                recordSet.append(dns.resource.ResourceRecord(rr_name, rr_type, rr_class, rr_ttl, rr_data))      
        
        return recordSet
