#!/usr/bin/env python3

""" Parsing and composing domain names

This module contains two classes for converting domain names to and from bytes.
You won't have to use these classes. They're used internally in Message,
Question, ResourceRecord and RecordData. You can read section 4.1.4 of RFC 1035
if you want more info.
"""

import struct


class Composer(object):
    def __init__(self):
        self.offsets = dict()
    
    def to_bytes(self, offset, dnames):
        # Convert each domain name in to bytes
        result = b""
        for i, dname in enumerate(dnames):
            # Split domain name into labels
            labels = dname.split(".")
            
            # Determine keys of subdomains in offset dict
            keys = []
            for label in reversed(labels):
                name = label
                if keys:
                     name += "." + keys[-1]
                keys.append(name)
            keys.reverse()

            # Convert label to bytes
            add_null = True
            for j, label in enumerate(labels):
                if keys[j] in self.offsets:
                    offset = self.offsets[keys[j]]
                    pointer = (3 << 14) + offset
                    result += struct.pack("!H", pointer)
                    add_null = False
                    offset += 2
                    break
                else:
                    self.offsets[keys[j]] = offset
                    result += struct.pack("!B{}s".format(len(label)),
                              len(label),
                              label)
                    offset += 1 + len(label)

            # Add null character at end
            if add_null:
                result += b"\x00"
                offset += 1

        return result


class Parser(object):
    def __init__(self):
        self.labels = dict()

    def from_bytes(self, packet, offset, num):
        begin_offset = offset
        dnames = []

        # Read the domain names
        for i in range(num):
            # Read a new domain name
            dname = ""
            prev_offsets = []
            done = False
            while done is False:
                # Read length of next label
                llength = struct.unpack_from("!B", packet, offset)[0]

                # Done reading domain when length is zero
                if llength == 0:
                    offset += 1
                    break
                
                # Compression label
                elif (llength >> 6) == 3:
                    new_offset = offset + 2
                    target = struct.unpack_from("!H", packet, offset)[0]
                    target -= 3 << 14
                    label = self.labels[target]
                    done = True

                # Normal label
                else:
                    new_offset = offset + llength + 1
                    label = struct.unpack_from("{}s".format(llength),
                            packet, offset+1)[0]

                # Add label to dictionary
                self.labels[offset] = label
                for prev_offset in prev_offsets:
                    self.labels[prev_offset] += "." + label
                prev_offsets.append(offset)

                # Update offset
                offset = new_offset

                # Append label to domain name
                if len(dname) > 0:
                    dname += "."
                dname += label

            # Append domain name to list
            dnames.append(dname)
        
        return dnames, offset
