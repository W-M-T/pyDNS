#!/usr/bin/env python2

"""A cache for resource records

This module contains a class which implements a cache for DNS resource records,
you still have to do most of the implementation. The module also provides a
class and a function for converting ResourceRecords from and to JSON strings.
It is highly recommended to use these.
"""

import json

from dns.resource import ResourceRecord, RecordData
from dns.types import Type
from dns.classes import Class
import dns.consts as Consts
import threading
import time

class ResourceEncoder(json.JSONEncoder):
    """ Conver ResourceRecord to JSON
    
    Usage:
        string = json.dumps(records, cls=ResourceEncoder, indent=4)
    """
    def default(self, obj):
        if isinstance(obj, ResourceRecord):
            return {
                "name": obj.name,
                "type": Type.to_string(obj.type_),
                "class": Class.to_string(obj.class_),
                "ttl": obj.ttl,
                "rdata": obj.rdata.data
            }
        return json.JSONEncoder.default(self, obj)


def resource_from_json(dct):
    """ Convert JSON object to ResourceRecord
    
    Usage:
        records = json.loads(string, object_hook=resource_from_json)
    """
    name = dct["name"]
    type_ = Type.from_string(dct["type"])
    class_ = Class.from_string(dct["class"])
    ttl = dct["ttl"]
    rdata = RecordData.create(type_, dct["rdata"])
    return ResourceRecord(name, type_, class_, ttl, rdata)


class RecordCache(object):
    """ Cache for ResourceRecords """

    def __init__(self, ttl):
        """ Initialize the RecordCache
        
        Args:
            ttl (int): TTL of cached entries (if > 0)
        """
        self.records = []
        self.ttl = ttl
        self.lock = threading.Lock()

        #Lees de cache in, update de ttls, gooi alle invalid data weg
        self.read_cache_file()
        self.fixDelta()

    def fixDelta(self):
        #Gebruik de het verschil tussen de huidige tijd en de timestamp van de net ingeladen cache om de ttl van alle records te updaten
        try:
            with open(Consts.CACHE_TIMESTAMP) as infile:
                oldtime = infile.read()
                nowtime = int(time.time())
                delta = nowtime - oldtime

                #update ttls
                self.lock.acquire()
                for entry in self.records:
                    entry.ttl = entry.ttl - delta
                self.lock.release()

                #gooi de entries weg met ttl <=0
                self.lock.acquire()
                records = [entry for entry in records if entry.ttl > 0]
                self.lock.acquire()

                self.lastCleanup = int(time.time())
                
                
        except (ValueError, IOError), e:
            print("An error has occured while updating the ttl's with the delta " + str(e))
    
    def cleanup(self):
        #Itereer over alle records, update hun ttls en gooi alle records weg waar deze <=0 wordt.

        nowtime = int(time.time())
        delta = nowtime - self.lastCleanup
        
        #update ttls
        self.lock.acquire()
        for entry in self.records:
            entry.ttl = entry.ttl - delta
        self.lock.release()

        #gooi de entries weg met ttl <=0
        self.lock.acquire()
        records = [entry for entry in records if entry.ttl > 0]
        self.lock.acquire()

        self.lastCleanup = int(time.time())
    
    def lookup(self, dname, type_, class_):
        """ Lookup resource records in cache

        Lookup for the resource records for a domain name with a specific type
        and class.
        
        Args:
            dname (str): domain name
            type_ (Type): type
            class_ (Class): class
        """
        results = []
        #Hier doen dat als hij een hit heeft maar de TTL verlopen is
        #dat hij dan onthoudt dat hij hem eruit moet gooien als hij
        #klaar is met itereren? We kunnen ook doen dat iets (anders)
        #actief de TTLs zit te bekijken en oude er uit gooit.
        for entry in self.records:
            if entry.dname == dname and entry.type_ == type_ and entry.class_ == class_:
                results.append(entry)
        return results
    
    def add_record(self, record):
        """ Add a new Record to the cache
        
        Args:
            record (ResourceRecord): the record added to the cache
        """
        #Only append if not already in cache
        #TODO: iets met TTL?
        #Zet de ttl niet op de gekregen waarde, maar op de gekregen waarde + de offset van de laatste cleanup
        #Anders wordt het te vroeg gecleaned

        #Wat als het al voorkomt? ttl updaten?
        self.lock.acquire()
        if not self.lookup(record.name, record.type_, record.class_):
            self.records.append(record)
        self.lock.release()
    
    def read_cache_file(self):
        """ Read the cache file from disk """
        #Empty current cache
        self.records = []

        #Load from file
        try:
            with open(Consts.CACHE_FILE) as infile:    
                data = infile.read()
                self.records = json.loads(data, object_hook=resource_from_json)
        except (ValueError, IOError), e:
            print("An error has occured while loading cache from disk: " + str(e))
            self.records = []
            #Gaat dit al fout als de file niet bestaat?


    def write_cache_file(self):
        """ Write the cache file to disk """
        cleanup()
        
        try:
            with open(Consts.CACHE_FILE, 'w') as outfile:
                outfile.write(string = json.dumps(records, cls=ResourceEncoder, indent=4))
            encoder = json.JSONEncoder()
            with open(Consts.CACHE_TIMESTAMP, 'w') as outfile:
                outfile.write(self.lastCleanup)
        except IOError, e:
            print("An error has occured while writing cache to disk: " + str(e))
