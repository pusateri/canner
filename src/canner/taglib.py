#
# Copyright 2007 !j Incorporated
#
# This file is part of Canner.
#
# Canner is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Canner.  If not, see <http://www.gnu.org/licenses/>.
#

# $Id: $

from __future__ import with_statement

import os
import sys
import re
import simplejson
import IPy; IPy.check_addr_prefixlen = False

_tags = []


class Tag(object):
    @classmethod
    def ip_address(cls, address, kind=None, **kw):
        ip = IPy.IP(address)
        name = ip.strCompressed(wantprefixlen=0)
        if ip.version() == 4:
            if not kind: kind = "IPv4 address"
            sort_name = "%08x" % ip.int()
        else:
            if not kind: kind = "IPv6 address"
            sort_name = "%032x" % ip.int()
        return cls(kind, name, sort_name=sort_name, **kw)

    @classmethod
    def ip_subnet(cls, address, kind=None, **kw):
        ip = IPy.IP(address, make_net=True)
        ip.NoPrefixForSingleIp = False
        name = ip.strCompressed()
        if ip.version() == 4:
            if not kind: kind = "IPv4 subnet"
            sort_name = "%08x/%02d" % (ip.int(), ip.prefixlen())
        else:
            if not kind: kind = "IPv6 subnet"
            sort_name = "%032x/%03d" % (ip.int(), ip.prefixlen())
        return cls(kind, name, sort_name=sort_name, **kw)    
    
    
    def __init__(self, kind=None, name=None, qname=None, 
                 sort_name=None, display_name=None):
        if qname:
            if kind or name:
                raise ValueError("kind and name cannot be used with qname")
            self.qname = qname
            self.kind, _, self.name = qname.partition("--")
        else:
            if not kind or not name:
                raise ValueError("kind and name must both be specified")
            self.qname = "%s--%s" % (kind, name)
            self.kind, self.name = kind, name
        self.sort_name = sort_name
        self.display_name = display_name
        self.entries = dict()
        
        global _tags
        _tags.append(self)

    def used(self, line=None, filename=None, sort_name=None, display_name=None):
        entry = self._entry_for_location(line, filename)
        if sort_name:
            self.sort_name = sort_name
            entry["sort name"] = sort_name
        if display_name:
            self.display_name = display_name
            entry["display name"] = display_name
        return self

    def implies(self, tag, line=None, filename=None):
        entry = self._entry_for_location(line, filename)
        try:
            lst = entry["implies"]
            if not isinstance(lst, list):
                lst = [lst]
            lst.append(tag.qname)
        except KeyError:
            entry["implies"] = tag.qname
        return self

    def implied_by(self, tag, line=None, filename=None):
        entry = self._entry_for_location(line, filename)
        try:
            lst = entry["implied by"]
            if not isinstance(lst, list):
                lst = [lst]
            lst.append(tag.qname)
        except KeyError:
            entry["implied by"] = tag.qname
        return self
        

    def _location(self, line=None, filename=None):
        global default_filename
        if not filename:
            filename = default_filename
        if filename and line:
            return "%s:%d" % (filename, line)
        elif filename:
            return filename
        raise ValueError("unknown location")
        
    def _entry_for_location(self, line, filename):
        location = self._location(line, filename)
        try:
            return self.entries[location]
        except KeyError:
            entry = dict(tag=self.qname, location=location)
            if not self.entries:  # This will be the first entry
                if self.sort_name:
                    entry["sort name"] = self.sort_name
                if self.display_name:
                    entry["display name"] = self.display_name
            self.entries[location] = entry
            return entry



def output_tags():
    all_entries = []
    for tag in _tags:
        all_entries.extend(tag.entries.values())
    simplejson.dump(all_entries, sys.stdout, indent=2, sort_keys=True)
    print



class _EnvironmentTags(object):
    @property
    def snapshot(self):
        try:
            return self._snapshot
        except AttributeError:
            session_id = os.environ.get("SESSION_ID", "unknown")
            self._snapshot = Tag("snapshot ID", session_id)
            return self._snapshot
        
    @property
    def device(self):
        try:
            return self._device
        except AttributeError:
            session_device = os.environ.get("SESSION_DEVICE", "unknown")
            self._device = Tag("snapshot device", session_device)
            return self._device
        
    @property
    def trigger(self):
        try:
            return self._trigger
        except AttributeError:
            trigger = os.environ.get("TRIGGER_TAG", "unknown")
            self._trigger = Tag(qname=trigger)
            return self._trigger

envtags = _EnvironmentTags()

default_filename = os.environ.get("TRIGGER_FILENAME", None)
