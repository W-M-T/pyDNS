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
    
    def cleanup(self):
        #Itereer over alle records, update hun ttls en gooi alle records weg waar deze <=0 wordt.
        
        #update ttls en timestamps
        self.lock.acquire()
        for i,e in enumerate(self.records):
            now = int(time.time())
            e[1].ttl = e[1].ttl - (now - e[0])#entry kan direct worden aangepast, omdat het een object is. timestamp echter niet, omdat het een int is
            self.records[i][0] = now #update de timestamp
        self.lock.release()

        #gooi de entries weg met ttl <=0
        self.lock.acquire()
        self.records = [(timestamp, entry) for (timestamp, entry) in self.records if entry.ttl > 0]
        self.lock.release()

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
        if (int(time.time()) - lastCleanup >= 3600)#Cache al een uur lang niet gecleaned
            self.cleanup()
        
        matchindexes = [i for i, e in self.records if e[1].dname == dname and e[1].type_ == type_ and e[1].class_ == class_]
        for i in matchindexes:
            now = int(time.time())
            temp = self.records[i]
            temp[1].ttl = temp[1].ttl - (now - temp[0])
            temp[0] = now
            self.records[i] = temp
        
        return [i for i, e in self.records if entry.dname == dname and entry.type_ == type_ and entry.class_ == class_ and entry.ttl - (int(time.time()) - timestamp) > 0]
        
    def add_record(self, record):
        """ Add a new Record to the cache
        
        Args:
            record (ResourceRecord): the record added to the cache
        """

        self.lock.acquire()
        found = self.lookup(record.name, record.type_, record.class_)
        if not found:
            self.records.append((int(time.time()), record))
        else:#Als het al in de cache zit, update dan alleen de ttls
            for i, e in enumerate(self.records):#We itereren over de enumeratie zodat we elementen kunnen manipuleren
                if e[1].dname == dname and e[1].type_ == type_ and e[1].class_ == class_:
                    now = time.time()
                    if (now + record.ttl > e[0] + e[1].ttl) #Als de nieuwe record hetzelfde is maar een hogere ttl heeft update de ttl
                    temp = e
                    temp[0] = now
                    temp[1].ttl = record.ttl
                    self.records[i] = temp
        self.lock.release()
    
    def read_cache_file(self):
        """ Read the cache file from disk """
        #Empty current cache
        self.records = []

        #Load from file
        try:
            with open(Consts.CACHE_FILE) as infile:
                with open(Consts.CACHE_TIMESTAMP) as stampfile:
                    data = infile.read()
                    last_timestamp = stampfile.read()
                    timestamp = int(time.time())
                    
                    recordlist = json.loads(data, object_hook=resource_from_json)

                    #update de ttls
                    for entry in recordlist
                        entry.ttl = entry.ttl - (timestamp - last_timestamp)

                    #gooi alle expired entries weg
                    recordlist = [entry for entry in recordlist if entry.ttl > 0]

                    #sla de entries op met een timestamp die aangeeft vanaf welk absoluut punt de ttl telde
                    self.records = [(timestamp, entry) for entry in recordlist]

        except (ValueError, IOError), e:
            print("An error has occured while loading cache from disk: " + str(e))
            self.records = []
            #Gaat dit al fout als de file niet bestaat?


    def write_cache_file(self):
        """ Write the cache file to disk """
        self.cleanup()
        
        try:
            with open(Consts.CACHE_FILE, 'w') as outfile:
                outfile.write(string = json.dumps([entry for (stamp, entry) in self.records], cls=ResourceEncoder, indent=4))
            encoder = json.JSONEncoder()
            with open(Consts.CACHE_TIMESTAMP, 'w') as outfile:
                outfile.write(int(time.time()))
        except IOError, e:
            print("An error has occured while writing cache to disk: " + str(e))
