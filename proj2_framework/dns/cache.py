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
                "rdata": obj.rdata.data,
                "timestamp": obj.timestamp
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
    timestamp = dct["timestamp"]
    return ResourceRecord(name, type_, class_, ttl, rdata, timestamp)


class RecordCache(object):
    """ Cache for ResourceRecords """

    def __init__(self):
        """ Initialize the RecordCache
        
        Args:
            ttl (int): TTL of cached entries (if > 0)
        """
        self.records = []
        self.lock = threading.Lock()

        #Lees de cache in, update de ttls, gooi alle invalid data weg
        self.read_cache_file()
        self.lastCleanup = time.time()
    
    def cleanup(self):
        """ Remove all entries in the cache whose TTL has expired """

        #gooi de entries weg met ttl <=0
        self.lock.acquire()
     	curTime = int(time.time())
        self.records = [record for record in self.records if record.ttl + record.timestamp > curTime]
        self.lock.release()

        self.lastCleanup = curTime
    
    def lookup(self, dname, type_, class_):
        """ Lookup resource records in cache

        Lookup for the resource records for a domain name with a specific type
        and class.
        
        Args:
            dname (str): domain name
            type_ (Type): type
            class_ (Class): class
        """

        if (int(time.time()) - self.lastCleanup >= 3600): #Cache al een uur lang niet gecleaned
            self.cleanup()

        foundrecords = [record for record in self.records \
        		if record.name == dname and record.type_ == type_ and record.class_ == class_ \
        		and record.ttl > time.time()]
        
        #Verschuif de ttl en timestamp naar nu
        curTime = int(time.time())
        for record in foundrecords:
            record.ttl = int(record.ttl - (curTime - record.timestamp))
            record.timestamp = curTime
            
        return foundrecords
        
    def add_record(self, new_rec):
        """ Add a new Record to the cache
        
        Args:
            record (ResourceRecord): the record added to the cache
        """

        self.lock.acquire()
        found = self.lookup(new_rec.name, new_rec.type_, new_rec.class_)
        if found:
            for record in self.records:#Het zou er maar 1 mogen zijn, maar bij een foute json-file kunnen het er meerdere zijn
                if (record.ttl + record.timestamp < new_rec.ttl + new_rec.timestamp):
                    record.ttl = new_rec.ttl
                    record.timestamp = new_rec.timestamp
        else:
            self.records.append(new_rec)
        self.lock.release()

    def read_cache_file(self, cache_file=Consts.CACHE_FILE):
        """ Read the cache file from disk """
        #Empty current cache
        self.records = []

        #Load from file
        try:
            with open(cache_file) as infile:
                data = infile.read()
                curTime = int(time.time())
                
                recordlist = json.loads(data, object_hook=resource_from_json)

                #Don't add the entries whose TTL is expired
                recordlist = [entry for entry in recordlist if entry.ttl + entry.timestamp > curTime]

                #Save all entries together with the time from which the TTL counts
                self.records = recordlist

        except (ValueError, IOError), e:
            #print("An error has occured while loading cache from disk: " + str(e))
            with open(cache_file, 'w') as outfile:
                outfile.write(json.dumps(self.records, cls=ResourceEncoder, indent=4))
            self.records = []

    def write_cache_file(self):
        """ Write the cache file to disk """
        self.cleanup()
        
        try:
            with open(Consts.CACHE_FILE, 'w') as outfile:
                outfile.write(json.dumps(self.records, cls=ResourceEncoder, indent=4))
        except IOError, e:
            print("An error has occured while writing cache to disk: " + str(e))
