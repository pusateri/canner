#!/usr/bin/env python
# encoding: utf-8

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

# $Id: parse-config.py 11 2008-01-25 14:44:19Z pusateri $

"""
parse-config.py
"""

import sys, os, re
from canner import taglib

# TODO: pim, syslog, flowstats, ipforwarding, ipmcforwarding, snmp, unallocated ports

def main(filename):
    lines = open(filename, 'rU')
    
    n = 0
    for line in lines:
        n += 1
        
        if re.match(r'Syntax error at token detail', line):
            lines.close()
            main(re.sub(r'-detail', '', filename))
            return

        # time
        m = re.match(r'configure sntp-client (primary|secondary) (?:server )? "?([\w\d.-]+)"?( vr [\w\d.]+)?', line)
        if m:
            which, server, vr = m.groups()
            taglib.tag("NTP server", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # dns
        m = re.match(r'configure dns-client add name-server ([\w\d.-]+)( vr [\w\d.]+)?', line)
        if m:
            server, vr = m.groups()
            taglib.tag("name server", server).implied_by(taglib.env_tags.device, line=n)
            continue
        m = re.match(r'configure dns-client add domain-suffix ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.tag("domain name", server).implied_by(taglib.env_tags.device, line=n)
            continue

        # interfaces
        m = re.match(r'create vlan "?([\w\d.-]+)"?', line)
        if m:
            vlan = m.group(1)
            vlanTag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            vlanTag.implied_by(taglib.env_tags.snapshot, line=n)
            taglib.env_tags.device.implied_by(vlanTag, line=n)
            continue
        m = re.match(r'configure vlan "?([\w\d]+)"? tag ([\d]+)', line)
        if m:
            vlan, vlan_id = m.group(1), int(m.group(2))
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            vlan_id_tag = taglib.tag("VLAN ID", vlan_id, sort_name="%05d" % vlan_id)
            vlan_tag.implied_by(taglib.env_tags.snapshot, line=n)
            vlan_tag.implies(taglib.env_tags.device, line=n)
            vlan_tag.implies(vlan_id_tag, line=n)
            continue
        m = re.match(r'config(?:ure)? vlan "?([\w\d]+)"? ipaddress ([\d.]+)\s+([\d.]+)\s+', line)
        if m:
            vlan, ipaddress, mask = m.groups()
            address = ipaddress + "/" + mask
            address_tag = taglib.ip_address_tag(address)
            subnet_tag = taglib.ip_subnet_tag(address)
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            vlan_tag.implied_by(taglib.env_tags.snapshot, line=n)
            vlan_tag.implies(taglib.env_tags.device, line=n)
            vlan_tag.implies(address_tag, line=n)
            address_tag.implies(subnet_tag, line=n)
            continue
        m = re.match(r'configure "?([\w\d]+)"? ipaddress ([a-fA-F\d:]+)/([\d]+)\s+', line)
        if m:
            vlan, ipaddress, mask = m.groups()
            address = ipaddress + "/" + mask
            address_tag = taglib.ip_address_tag(address, "IPv6 address")
            subnet_tag = taglib.ip_subnet_tag(address, "IPv6 subnet")
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            vlan_tag.implied_by(taglib.env_tags.snapshot, line=n)
            vlan_tag.implies(taglib.env_tags.device, line=n)
            vlan_tag.implies(address_tag, line=n)
            address_tag.implies(subnet_tag, line=n)
            continue

        # dhcp/bootp
        m = re.match(r'configure bootprelay add ([\w\d.-]+)', line)
        if m:
            relay = m.group(1)
            taglib.tag("BOOTP relay", relay).implied_by(taglib.env_tags.device, line=n)
            continue

        # accounts
        m = re.match(r'create account (admin|user) "?([\w\d.-]+)"?\s+.*', line)
        if m:
            account = m.group(2)
            taglib.tag("user", account).implied_by(taglib.env_tags.device, line=n)
            continue
        m = re.match(r'configure account (admin|user).*', line)
        if m:
            account = m.group(1)
            taglib.tag("user", account).implied_by(taglib.env_tags.device, line=n)
            continue

        # protocols
        m = re.match(r'enable (bgp|igmp|MLD|msdp|rip|ripng)$', line)
        if m:
            protocolTag = taglib.tag("routing protocol", protocol_name(m.group(1)))
            protocolTag.implied_by(taglib.env_tags.device, line=n)
            continue
        m = re.match(r'enable (igmp|MLD) snooping.*', line)
        if m:
            protocol = m.group(1)
            protocolTag = taglib.tag("routing protocol", taglib.protocol_name(protocol))
            protocolTag.implied_by(taglib.env_tags.device, line=n)
            continue
        m = re.match(r'configure DVMRP add vlan "?([\w\d.-]+)"?', line)
        if m:
            vlan = m.group(1)
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            taglib.tag("routing protocol", "DVMRP").implied_by(vlan_tag, n)
            continue
        m = re.match(r'configure ospf add vlan "?([\w\d.-]+)"? area ([\d.]+).*', line)
        if m:
            vlan, area = m.groups()
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            area_tag = taglib.tag("OSPF area", area)
            area_tag.implied_by(vlan_tag, line=n)
            area_tag.implies(taglib.tag("routing protocol", "OSPF"), line=n)
            continue
        m = re.match(r'configure ospf vlan ([\w\d.-]+) area ([\d.]+)', line)
        if m:
            vlan, area = m.groups()
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            area_tag = taglib.tag("OSPF area", area)
            area_tag.implied_by(vlan_tag, line=n)
            area_tag.implies(taglib.tag("routing protocol", "OSPF"), line=n)
            continue
        m = re.match(r'configure ospfv3 domain ([\w\d.-]+) add vlan ([\w\d.-]+) instance-id ([\d]+) area ([\d.]+)', line)
        if m:
            domain, vlan, instance, area = m.groups()
            vlan_tag = taglib.tag("interface", "%s %s" % (taglib.env_tags.device.name, vlan))
            area_tag = taglib.tag("OSPFv3 area", area)
            area_tag.implied_by(vlan_tag, line=n)
            area_tag.implies(taglib.tag("routing protocol", "OSPFv3"), line=n)
            continue

        # services
        serviceLabelDict = {'ssh':'SSHv1', 'ssh1':'SSHv1', 'ssh2':'SSHv2', 'telnet':'TELNET',
                            'web':'HTTP'}
        m = re.match(r'enable (ssh2|telnet|web)( access-profile ([\w\d.-]+)( port ([\d]+))?)?', line)
        if m:
            service = m.group(1)
            taglib.tag("service", serviceLabelDict[service]).implied_by(taglib.env_tags.device, n)
            continue
        m = re.match(r'configure telnet( access-profile ([\w\d.-]+))?( port ([\d]+))?( vr ([\w\d.-]+))?', line)
        if m:
            taglib.tag("service", "TELNET").implied_by(taglib.env_tags.device, n)
            continue


if __name__ == '__main__':
    main(taglib.default_filename)
    taglib.output_tagging_log()
