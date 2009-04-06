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
    ssh_version = None
    ssh_enable = False
    for line in lines:
        n += 1

        # hostname
        m = re.match(r'set hostname ([\w\d.-]+)', line)
        if m:
            host = m.group(1)
            taglib.tag("hostname", host).implied_by(taglib.env_tags.device, line=n)
            continue
        
        # time
        m = re.match(r'set ntp server( backup\d)? "?([\w\d.-]+)"?', line)
        if m:
            server = m.group(2)
            if not server == '0.0.0.0':
                taglib.tag("NTP server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # dns
        m = re.match(r'set domain ([\w\d.-]+)', line)
        if m:
            domain = m.group(1)
            taglib.tag("domain name", domain).implied_by(taglib.env_tags.device, line=n)
            continue
            
        m = re.match(r'set dns host dns\d ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.tag("name server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        m = re.match(r'set xauth ([\w\d.-]+) dns\d ([\w\d.-]+)', line)
        if m:
            server = m.group(2)
            taglib.tag("name server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        m = re.match(r'set l2tp dns\d ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.tag("name server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # interfaces
        m = re.match(r'set interface ([\w\d]+) ip ([\d.]+)/([\d.]+)( secondary)?', line)
        if m:
            name, ipaddress, plen, secondary = m.groups()
            address = ipaddress + "/" + plen
            ifaddr_tag = taglib.ip_address_tag(address, "interface address")
            address_tag = taglib.ip_address_tag(address)
            subnet_tag = taglib.ip_subnet_tag(address)
            name_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, name))
            name_tag.implied_by(taglib.env_tags.snapshot, line=n)
            name_tag.implies(taglib.env_tags.device, line=n)
            name_tag.implies(ifaddr_tag, line=n)
            ifaddr_tag.implies(address_tag, line=n)
            address_tag.implies(subnet_tag, line=n)
            continue

        # accounts
        m = re.match(r'set admin user "?([\w\d.-]+)"?\s+.*', line)
        if m:
            account = m.group(1)
            taglib.tag("user", account).implied_by(taglib.env_tags.device, line=n)
            continue

        # services
        m = re.match(r'set ssh version ([\w\d]+)', line)
        if m:
            ssh_version = m.group(1)
            ssh_version_line = n
            continue

        m = re.match(r'set ssh enable', line)
        if m:
            ssh_enable = True
            taglib.tag("service", 'SSH').implied_by(taglib.env_tags.device, n)
            continue

        m = re.match(r'set scp enable', line)
        if m:
            taglib.tag("service", 'SCP').implied_by(taglib.env_tags.device, n)
            continue

    # post parse phase
    if ssh_enable:
        if ssh_version:
            taglib.tag("service", 'SSH' + ssh_version).implied_by(taglib.env_tags.device, ssh_version_line)


if __name__ == '__main__':
    main(taglib.default_filename)
    taglib.output_tagging_log()
