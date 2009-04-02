#!/usr/bin/env python
# encoding: utf-8

#
# Copyright 2009 !j Incorporated
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

"""
parse-config.py
"""

import sys, os, re
from canner import taglib


def main(filename):
    lines = open(filename, 'rU')
    
    n = 0
    for line in lines:
        n += 1
        
        if re.match(r'Syntax error at token detail', line):
            lines.close()
            taglib.default_filename = filename = re.sub(r'-detail', '', filename)
            main(filename)
            return

        # time
        m = re.match(r'set ntp server "?([\w\d.-]+)"?( key [\d]+)?', line)
        if m:
            server, key = m.groups()
            taglib.tag("NTP server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # dns
        m = re.match(r'set ip dns domain ([\w\d.-]+)', line)
        if m:
            domain = m.group(1)
            taglib.tag("domain name", domain).implied_by(taglib.env_tags.device, line=n)
            continue
            
        m = re.match(r'set ip dns server ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.tag("name server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # radius
        m = re.match(r'set radius server ([\w\d.-]+)\s+auth-port ([\d]+)( acct-port [\d]+)?( primary)?', line)
        if m:
            server, port, acct, which = m.groups()
            taglib.tag("RADIUS server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # tacacs+
        m = re.match(r'set tacacs server ([\w\d.-]+)( primary)?', line)
        if m:
            server, which = m.groups()
            taglib.tag("TACACS+ server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # interfaces
        m = re.match(r'set interface "?([\w\d]+)"? ([\d]+)\s+([\d.]+)/([\d.]+)\s+([\d.]+)', line)
        if m:
            vlan, vlan, ipaddress, mask, broadcast = m.groups()
            address = ipaddress + "/" + mask
            ifaddr_tag = taglib.ip_address_tag(address, "interface address")
            address_tag = taglib.ip_address_tag(address)
            subnet_tag = taglib.ip_subnet_tag(address)
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            vlan_tag.implied_by(taglib.env_tags.snapshot, line=n)
            vlan_tag.implies(taglib.env_tags.device, line=n)
            vlan_tag.implies(ifaddr_tag, line=n)
            ifaddr_tag.implies(address_tag, line=n)
            address_tag.implies(subnet_tag, line=n)
            continue

        # accounts
        m = re.match(r'set localuser user "?([\w\d.-]+)"?\s+.*', line)
        if m:
            account = m.group(1)
            taglib.tag("user", account).implied_by(taglib.env_tags.device, line=n)
            continue

        # services
        m = re.match(r'set ip http server enable', line)
        if m:
            taglib.tag("service", 'HTTP').implied_by(taglib.env_tags.device, n)
            continue

if __name__ == '__main__':
    main(taglib.default_filename)
    taglib.output_tagging_log()
