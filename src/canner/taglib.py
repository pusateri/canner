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

from __future__ import with_statement

import os
import sys
import re
import simplejson
import IPy; IPy.check_addr_prefixlen = False



class Tag(object):
    def __init__(self, kind=None, name=None, sort_name=None, display_name=None):
        self.kind = kind
        self.name = name
        self.sort_name = sort_name
        self.display_name = display_name
        self.qname = "%s--%s" % (kind, name)
        self.changes = dict(never_flushed=True,
                            sort_name=sort_name, 
                            display_name=display_name)
        
    def used(self, line=None, filename=None, sort_name=None, display_name=None):
        if sort_name:
            self.sort_name = self.changes["sort_name"] = sort_name
        if display_name:
            self.display_name = self.changes["display_name"] = display_name
        self._flush_changes(line, filename)
        return self

    def implies(self, tag, line=None, filename=None):
        self.changes["implies"] = tag.qname
        self._flush_changes(line, filename)
        return self

    def implied_by(self, tag, line=None, filename=None):
        self.changes["implied_by"] = tag.qname
        self._flush_changes(line, filename)
        return self

    logging_function = None
    
    def _flush_changes(self, line, filename):
        if self.logging_function:
            entry = dict((k, v) for k, v in self.changes.iteritems() if v)
            if entry:
                entry["tag"] = self.qname
                if "never_flushed" in entry:
                    # never_flushed is just to force an initial flush.
                    del entry["never_flushed"]
                if not filename:
                    filename = default_filename
                if filename and line:
                    entry["location"] = "%s:%d" % (filename, line)
                elif filename:
                    entry["location"] = filename
                else:
                    raise ValueError("unknown location")
                self.logging_function(entry)
        self.changes = dict()



_known_tags = dict()

def tag(kind=None, name=None, qname=None, **kw):
    if qname:
        if kind or name:
            raise ValueError("kind and name cannot be used with qname")
        kind, _, name = qname.partition("--")
    else:
        if not kind or not name:
            raise ValueError("kind and name must both be specified")
        qname = "%s--%s" % (kind, name)
    try:
        return _known_tags[qname]
    except KeyError:
        t = _known_tags[qname] = Tag(kind, name, **kw)
        return t

def ip_address_tag(address, kind=None, subnet_also=True, **kw):
    ip = IPy.IP(address)
    name = ip.strCompressed(wantprefixlen=0)
    if ip.version() == 4:
        if not kind: kind = "IPv4 address"
        sort_name = "v4 %08x" % ip.int()
    else:
        if not kind: kind = "IPv6 address"
        sort_name = "v6 %032x" % ip.int()
    return tag(kind, name, sort_name=sort_name, **kw)

def ip_subnet_tag(address, kind=None, **kw):
    ip = IPy.IP(address, make_net=True)
    ip.NoPrefixForSingleIp = False
    name = ip.strCompressed()
    if ip.version() == 4:
        if not kind: kind = "IPv4 subnet"
        sort_name = "v4 %08x/%02d" % (ip.int(), ip.prefixlen())
    else:
        if not kind: kind = "IPv6 subnet"
        sort_name = "v6 %032x/%03d" % (ip.int(), ip.prefixlen())
    return tag(kind, name, sort_name=sort_name, **kw)    



_tagging_log = list()

def _add_to_tagging_log(tag_self, entry):
    _tagging_log.append(entry)
Tag.logging_function = _add_to_tagging_log    

def output_tagging_log():
    simplejson.dump(_tagging_log, sys.stdout, indent=2, sort_keys=True)
    print



default_filename = os.environ.get("TRIGGER_FILENAME", None)


class _EnvironmentTags(object):
    @property
    def snapshot(self):
        try:
            return self._snapshot
        except AttributeError:
            session_id = os.environ.get("SESSION_ID", "unknown")
            self._snapshot = tag("snapshot", session_id)
            return self._snapshot
        
    @property
    def device(self):
        try:
            return self._device
        except AttributeError:
            session_device = os.environ.get("SESSION_DEVICE", "unknown")
            self._device = tag("device", session_device)
            return self._device
        
    @property
    def trigger(self):
        try:
            return self._trigger
        except AttributeError:
            kind = os.environ.get("TRIGGER_KIND", "unknown")
            name = os.environ.get("TRIGGER_NAME", "unkonwn")
            self._trigger = tag(kind, name)
            return self._trigger

env_tags = _EnvironmentTags()



def protocol_name(name):
    protocol_names = {
        'bgp':'BGP', 'dhcp':'DHCP', 'finger':'FINGER', 'ftp':'FTP',
        'http':'HTTP', 'https':'HTTPS', 'igmp':'IGMP', 'MLD':'MLD', 
        'mpls':'MPLS', 'msdp':'MSDP', 'netconf':'NETCONF', 'ospf':'OSPF', 
        'pim':'PIM', 'rip':'RIP', 'ripng':'RIPng', 'scp':'SCP', 
        'service-deployment':'SDXD', 'ssh':'SSH', 'telnet':'TELNET', 
        'telnets':'TELNETS', 'xnm-clear-text':'XNM', 'xnm-ssl':'XNMS'
        }
    return protocol_names.get(name, name)
