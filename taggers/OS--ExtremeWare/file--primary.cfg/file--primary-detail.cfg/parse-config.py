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

# $Id$

"""
parse-config.py
"""

import sys, os, re
from canner import taglib
from canner.taglib import *

snapshotID = os.environ.get("SESSION_ID", "unknown")
snapshotIDTag = "snapshot ID--%s" % snapshotID
snapshotDevice = os.environ.get("SESSION_DEVICE", "unknown")
snapshotDeviceTag = "snapshot device--%s" % snapshotDevice

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
        m = re.match(r'configure sntp-client (primary|secondary) server "?([\w\d.-]+)"?', line)
        if m:
            which, server = m.groups()
            taglib.output_tag(filename, n, 'NTP server--%s' % server, context=snapshotDeviceTag)
            continue

        # dns
        m = re.match(r'configure dns-client add name-server ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.output_tag(filename, n, 'name server--%s' % server, context=snapshotDeviceTag)
            continue
        m = re.match(r'configure dns-client add domain-suffix ([\w\d.-]+)', line)
        if m:
            server = m.group(1)
            taglib.output_tag(filename, n, 'domain name--%s' % server, context=snapshotDeviceTag)
            continue

        # interfaces
        m = re.match(r'create vlan "?([\w\d.-]+)"?', line)
        if m:
            vlan = m.group(1)
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            taglib.output_tag(filename, n, vlanTag, context=snapshotIDTag)
            taglib.output_tag(filename, n, snapshotDeviceTag, context=vlanTag)
            continue
        m = re.match(r'configure vlan "?([\w\d]+)"? tag ([\d]+)', line)
        if m:
            vlan, vlanID = m.group(1), int(m.group(2))
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            taglib.output_tag(filename, n, vlanTag, context=snapshotIDTag)
            taglib.output_tag(filename, n, snapshotDeviceTag, context=vlanTag)
            vlanIDTag = "VLAN ID--%d" % vlanID
            taglib.output_tag(filename, n, vlanIDTag,
                              sortName="%04d" % vlanID,
                              context=vlanTag)
            continue
        m = re.match(r'config(?:ure)? vlan "?([\w\d]+)"? ipaddress ([\d.]+)\s+([\d.]+)\s+', line)
        if m:
            vlan, ipaddress, mask = m.groups()
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            taglib.output_tag(filename, n, vlanTag, context=snapshotIDTag)
            taglib.output_tag(filename, n, snapshotDeviceTag, context=vlanTag)
            address = (ipaddress + '/' + mask)
            name, properties = ip_address(address)
            addressTag = "IPv4 interface address--%s" % name
            taglib.output_tag(filename, n, addressTag, properties, context=vlanTag)
            name, properties = ip_subnet(address)
            subnetTag = "IPv4 subnet--%s" % name
            taglib.output_tag(filename, n, subnetTag, properties, context=addressTag)
            continue
        m = re.match(r'configure "?([\w\d]+)"? ipaddress ([a-fA-F\d:]+)/([\d]+)\s+', line)
        if m:
            vlan, ipaddress, mask = m.groups()
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            address = (ipaddress + '/' + mask)
            name, properties = ip_address(address)
            addressTag = "IPv6 interface address--%s" % name
            taglib.output_tag(filename, n, addressTag, properties, context=vlanTag)
            name, properties = ip_subnet(address)
            subnetTag = "IPv6 subnet--%s" % name
            taglib.output_tag(filename, n, subnetTag, properties, context=addressTag)
            continue

        # dhcp/bootp
        m = re.match(r'configure bootprelay add ([\w\d.-]+)', line)
        if m:
            relay = m.group(1)
            taglib.output_tag(filename, n, 'BOOTP relay--%s' % relay, context=snapshotDeviceTag)
            continue

        # accounts
        m = re.match(r'create account (admin|user) "?([\w\d.-]+)"?\s+.*', line)
        if m:
            account = m.group(2)
            taglib.output_tag(filename, n, 'user--%s' % account, context=snapshotDeviceTag)
            continue
        m = re.match(r'configure account (admin|user).*', line)
        if m:
            account = m.group(1)
            taglib.output_tag(filename, n, 'user--%s' % account, context=snapshotDeviceTag)
            continue

        # protocols
        m = re.match(r'enable (bgp|igmp|MLD|msdp|rip|ripng)$', line)
        if m:
            protocolTag = 'routing protocol--%s' % protocol_name(m.group(1))
            taglib.output_tag(filename, n, protocolTag, context=snapshotDeviceTag)
            continue
        m = re.match(r'enable (igmp|MLD) snooping.*', line)
        if m:
            protocol = m.group(1)
            protocolTag = 'routing protocol--%s' % protocol_name(protocol)
            taglib.output_tag(filename, n, protocolTag, context=snapshotDeviceTag)
            continue
        m = re.match(r'configure DVMRP add vlan "?([\w\d.-]+)"?', line)
        if m:
            vlan = m.group(1)
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            taglib.output_tag(filename, n, 'routing protocol--DVMRP', context=vlanTag)
            continue
        m = re.match(r'configure ospf add vlan "?([\w\d.-]+)"? area ([\d.]+).*', line)
        if m:
            vlan, area = m.groups()
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            areaTag = 'OSPF area--%s' % area
            taglib.output_tag(filename, n, areaTag, context=vlanTag)
            taglib.output_tag(filename, n, 'routing protocol--OSPF', context=areaTag)
            continue
        m = re.match(r'configure ospf vlan ([\w\d.-]+) area ([\d.]+)', line)
        if m:
            vlan, area = m.groups()
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            areaTag = 'OSPF area--%s' % area
            taglib.output_tag(filename, n, areaTag, context=vlanTag)
            taglib.output_tag(filename, n, 'routing protocol--OSPF', context=areaTag)
            continue
        m = re.match(r'configure ospfv3 domain ([\w\d.-]+) add vlan ([\w\d.-]+) instance-id ([\d]+) area ([\d.]+)', line)
        if m:
            domain, vlan, instance, area = m.groups()
            vlanTag = "interface--%s %s" % (snapshotDevice, vlan)
            areaTag = 'OSPFv3 area--%s' % area
            taglib.output_tag(filename, n, areaTag, context=vlanTag)
            taglib.output_tag(filename, n, 'routing protocol--OSPFv3', context=areaTag)
            continue

        # services
        serviceLabelDict = {'ssh':'SSHv1', 'ssh1':'SSHv1', 'ssh2':'SSHv2', 'telnet':'TELNET',
                            'web':'HTTP'}
        m = re.match(r'enable (ssh2|telnet|web)( access-profile ([\w\d.-]+)( port ([\d]+))?)?', line)
        if m:
            service = m.group(1)
            serviceTag = 'service--%s' % serviceLabelDict[service]
            taglib.output_tag(filename, n, serviceTag, context=snapshotDeviceTag)
            continue

if __name__ == '__main__':
    main(sys.argv[1])
