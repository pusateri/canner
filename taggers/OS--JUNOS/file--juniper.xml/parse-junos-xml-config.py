#!/usr/bin/env python

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

# $Id: parse-junos-xml-config.py 7 2007-12-17 21:43:06Z pusateri $

from canner.taglib import *
import re
import IPy

tagPatterns = [
    ('system/domain-name',                    'domain name',       text),
    ('system/time-zone',                      'time zone',         text),
    ('system/name-server/name',               'name server',       text),
    ('system/radius-server/name',             'RADIUS server',     text),
    ('system/ntp/boot-server',                'NTP boot server',   text),
    ('system/ntp/server/name',                'NTP server',        text),
    ('system/login/user/name',                'user',              text),
    ('snmp/community/name',                   'SNMP community',    text),
]

ot = output_tag

allInterfaceTags = []

import os
snapshotID = os.environ.get("SESSION_ID", "unknown")
snapshotIDTag = "snapshot ID--%s" % snapshotID
snapshotDevice = os.environ.get("SESSION_DEVICE", "unknown")
snapshotDeviceTag = "snapshot device--%s" % snapshotDevice

def serviceTag(element, fn):
    serviceTag = "service--%s" % protocol_name(element.tag)
    ot(fn, element.sourceline, serviceTag, context=snapshotDeviceTag)

def serviceTags(top, fn):
    for elem in top.xpath("system/services/*"):
        if elem.tag == 'web-management':
            for proto in elem.xpath("*"):
                serviceTag(proto, fn)
        else:
            serviceTag(elem, fn)

def outputInterfaceTags(top, fn):
    for ifElem in top.xpath("interfaces/interface"):
        ifNameElem = ifElem.xpath("name")[0]
        ifTag = "physical interface--%s %s" % (snapshotDevice, ifNameElem.text)
        ot(fn, ifNameElem.sourceline, snapshotDeviceTag, context=ifTag)

        descrElems = ifElem.xpath("description")
        if descrElems:
            elem = descrElems[0]
            tag = "interface description--" + elem.text
            ot(fn, elem.sourceline, tag, context=ifTag)

        m = re.match(r"[a-zA-Z]+", ifNameElem.text)
        if m:
            ot(fn, ifNameElem.sourceline, "interface type--" + m.group(0),
               context=ifTag)

        for unitElem in ifElem.xpath("unit"):
            unitNameElem = unitElem.xpath("name")[0]
            unitName = ifNameElem.text + "." + unitNameElem.text
            unitTag = "interface--%s %s" % (snapshotDevice, unitName)
            ot(fn, unitNameElem.sourceline, unitTag, context=snapshotIDTag)
            ot(fn, ifNameElem.sourceline, ifTag, context=unitTag)

            allInterfaceTags.append(unitTag)

            vlanIDList = unitElem.xpath("vlan-id")
            if vlanIDList:
                id = int(vlanIDList[0].text)
                vlanIDTag = "VLAN ID--%d" % id
                ot(fn, vlanIDList[0].sourceline, vlanIDTag,
                   sortName="%04d" % id,
                   context=unitTag)

            descrElems = unitElem.xpath("description")
            if descrElems:
                elem = descrElems[0]
                tag = "interface description--" + elem.text
                ot(fn, elem.sourceline, tag, context=unitTag)


            def outputAddresses(familyElem, af):
                for addressNameElem in familyElem.xpath("address/name"):
                    name, properties = ip_address(addressNameElem.text)
                    addressTag = "%s interface address--%s" % (af, name)
                    ot(fn, addressNameElem.sourceline, addressTag, properties,
                        context=unitTag)

                    name, properties = ip_subnet(addressNameElem.text)
                    subnetTag = "%s subnet--%s" % (af, name)
                    ot(fn, addressNameElem.sourceline, subnetTag, properties,
                        context=addressTag)

            inetFamilyList = unitElem.xpath("family/inet")
            inetFamilyElem = inetFamilyList[0] if inetFamilyList else None
            inet6FamilyList = unitElem.xpath("family/inet6")
            inet6FamilyElem = inet6FamilyList[0] if inet6FamilyList else None

            if inetFamilyElem and inet6FamilyElem:
                ot(fn, inetFamilyElem.sourceline,
                   "address family--inet and inet6", context=unitTag)
                ot(fn, inet6FamilyElem.sourceline,
                   "address family--inet and inet6", context=unitTag)
                outputAddresses(inetFamilyElem, "IPv4")
                outputAddresses(inet6FamilyElem, "IPv6")
            elif inetFamilyElem:
                ot(fn, inetFamilyElem.sourceline, "address family--inet only",
                   context=unitTag)
                outputAddresses(inetFamilyElem, "IPv4")
            elif inet6FamilyElem:
                ot(fn, inet6FamilyElem.sourceline, "address family--inet6 only",
                   context=unitTag)
                outputAddresses(inet6FamilyElem, "IPv6")

def outputProtocols(top, fn):
    
    protocol = "BGP"
    protocolElemList = top.xpath("protocols/%s" % protocol.lower())
    if protocolElemList:
        protocolElem = protocolElemList[0]
        protocolTag = "routing protocol--%s" % protocol
        for groupElem in protocolElem.xpath("group"):
            nameElem = groupElem.xpath("name")[0]
            bgpGroupTag = "%s group--%s %s" % (protocol, snapshotDevice, nameElem.text)
            ot(fn, nameElem.sourceline, bgpGroupTag, context=snapshotDeviceTag)
            for neighborNameElem in groupElem.xpath("neighbor/name"):
                address = IPy.IP(neighborNameElem.text)
                if address.version() == 4:
                    af = 'IPv4'
                elif address.version() == 6:
                    af = 'IPv6'
                else:
                    break
                addressTag = "%s interface address--%s" % (af, neighborNameElem.text)
                peerTag = "%s peer--%s" % (protocol, neighborNameElem.text)
                ot(fn, neighborNameElem.sourceline, peerTag, context=addressTag)
                ot(fn, neighborNameElem.sourceline, peerTag, context=bgpGroupTag)
                ot(fn, protocolElem.sourceline, protocolTag, context=peerTag)
                # determine the AS number, if the peer doesn't have its own, use the groups
                asnElemList = neighborNameElem.xpath("peer-as")
                if len(asnElemList) == 0:
                    asnElemList = groupElem.xpath("peer-as")
                if len(asnElemList) > 0:
                    asnElem = asnElemList[0]
                    asnTag = "autonomous system--%s" % asnElem.text
                    ot(fn, asnElem.sourceline, asnTag, context=peerTag,
                       sortName='%010d' % int(asnElem.text))
            
        
    protocol = "MSDP"
    protocolElemList = top.xpath("protocols/%s" % protocol.lower())
    if protocolElemList:
        protocolElem = protocolElemList[0]
        protocolTag = "routing protocol--%s" % protocol
        for groupElem in protocolElem.xpath("group"):
            nameElem = groupElem.xpath("name")[0]
            msdpGroupTag = "%s group--%s %s" % (protocol, snapshotDevice, nameElem.text)
            for peerNameElem in groupElem.xpath("peer/name"):
                address = IPy.IP(peerNameElem.text)
                if address.version() == 4:
                    addressTag = "IPv4 interface address--%s" % peerNameElem.text
                    peerTag = "%s peer--%s" % (protocol, peerNameElem.text)
                    ot(fn, peerNameElem.sourceline, peerTag, context=addressTag)
                    ot(fn, peerNameElem.sourceline, peerTag, context=msdpGroupTag)
                    ot(fn, protocolElem.sourceline, protocolTag, context=peerTag)
            ot(fn, nameElem.sourceline, msdpGroupTag, context=snapshotDeviceTag)
    
    ospfVersionDict = {'OSPF':'OSPF', 'OSPF3':'OSPFv3'}
    for ospfVersion in ospfVersionDict.keys():
        ospfElemList = top.xpath("protocols/%s" % ospfVersion.lower())
        if not ospfElemList:
            break
        ospfElem = ospfElemList[0]
        ospfVersionLabel = ospfVersionDict[ospfVersion]
        protocolTag = "routing protocol--%s" % ospfVersionLabel
        for areaElem in ospfElem.xpath("area"):
            nameElem = areaElem.xpath("name")[0]
            ospfAreaTag = "%s area--%s" % (ospfVersionLabel, nameElem.text)
            for interfaceNameElem in areaElem.xpath("interface/name"):
                if interfaceNameElem.text == "all":
                    interfaceTags = allInterfaceTags
                else:
                    interfaceTags = ["interface--%s %s" % (snapshotDevice, interfaceNameElem.text)]
                for tag in interfaceTags:
                    ot(fn, interfaceNameElem.sourceline, ospfAreaTag, context=tag)
            ot(fn, nameElem.sourceline, protocolTag, context=ospfAreaTag)

    protocol = "PIM"
    protocolElemList = top.xpath("protocols/%s" % protocol.lower())
    if protocolElemList:
        protocolElem = protocolElemList[0]
        protocolTag = "routing protocol--%s" % protocol
        for interfaceNameElem in protocolElem.xpath("interface/name"):
            if interfaceNameElem.text == "all":
                interfaceTags = allInterfaceTags
            else:
                interfaceTags = ["interface--%s %s" % (snapshotDevice, interfaceNameElem.text)]
            for tag in interfaceTags:
                ot(fn, interfaceNameElem.sourceline, protocolTag, context=tag)

    for ripVersion in ("RIP", "RIPng"):
        ripElemList = top.xpath("protocols/%s" % ripVersion.lower())
        if not ripElemList:
            break
        ripElem = ripElemList[0]
        protocolTag = "routing protocol--%s" % ripVersion
        for groupElem in ripElem.xpath("group"):
            nameElem = groupElem.xpath("name")[0]
            ripGroupTag = "%s group--%s" % (ripVersion, nameElem.text)
            for interfaceNameElem in groupElem.xpath("neighbor/name"):
                if interfaceNameElem.text == "all":
                    interfaceTags = allInterfaceTags
                else:
                    interfaceTags = ["interface--%s %s" % (snapshotDevice, interfaceNameElem.text)]
                for tag in interfaceTags:
                    ot(fn, interfaceNameElem.sourceline, ripGroupTag, context=tag)
            ot(fn, nameElem.sourceline, protocolTag, context=ripGroupTag)


if __name__ == '__main__':
    main(tagPatterns, serviceTags, outputInterfaceTags, outputProtocols)
