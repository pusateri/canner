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

from __future__ import with_statement

import re
import sys
from lxml import etree
from canner import taglib

all_interface_tags = []

device_tag = taglib.env_tags.device
snapshot_tag = taglib.env_tags.snapshot

def tag_services(top):
    def service_tag(e):
        if not e.tag.endswith("}comment"):
            t = taglib.tag("service", taglib.protocol_name(e.tag))
            t.implied_by(taglib.env_tags.device, e.sourceline)
    for elem in top.xpath("system/services/*"):
        if elem.tag == 'web-management':
            for proto in elem.xpath("*"):
                service_tag(proto)
        else:
            service_tag(elem)

def tag_interfaces(top):
    for if_elem in top.xpath("interfaces/interface"):
        if_name_elem = if_elem.xpath("name")[0]
        if_tag = taglib.tag("physical interface", 
                           "%s %s" % (device_tag.name, if_name_elem.text))
        if_tag.implies(device_tag, if_name_elem.sourceline)

        descr_elems = if_elem.xpath("description")
        if descr_elems:
            elem = descr_elems[0]
            t = taglib.tag("interface description", elem.text)
            t.implied_by(if_tag, elem.sourceline)

        m = re.match(r"[a-zA-Z]+", if_name_elem.text)
        if m:
            t = taglib.tag("interface type", m.group(0))
            t.implied_by(if_tag, if_name_elem.sourceline)

        for unit_elem in if_elem.xpath("unit"):
            unit_name_elem = unit_elem.xpath("name")[0]
            unit_name = if_name_elem.text + "." + unit_name_elem.text
            unit_tag = taglib.tag("interface", "%s %s" % (device_tag.name, 
                                                         unit_name))
            unit_tag.implied_by(snapshot_tag, unit_name_elem.sourceline)
            unit_tag.implies(if_tag, unit_name_elem.sourceline)

            all_interface_tags.append(unit_tag)

            vlan_id_list = unit_elem.xpath("vlan-id")
            if vlan_id_list:
                vlan_id = int(vlan_id_list[0].text)
                vlan_id_tag = taglib.tag("VLAN ID", str(vlan_id), 
                                       sort_name="%05d" % vlan_id)
                vlan_id_tag.implied_by(unit_tag, vlan_id_list[0].sourceline)

            descr_elems = unit_elem.xpath("description")
            if descr_elems:
                elem = descr_elems[0]
                t = taglib.tag("interface description", elem.text)
                t.implied_by(unit_tag, elem.sourceline)


            def tag_addresses(family_elem):
                for address_elem in family_elem.xpath("address/name"):
                    ifa_tag = taglib.ip_address_tag(address_elem.text,
                                                    kind="interface address")
                    ifa_tag.implied_by(unit_tag, address_elem.sourceline)
                    t = taglib.ip_address_tag(address_elem.text)
                    t.implied_by(ifa_tag, address_elem.sourceline)
                    t.implies(taglib.ip_subnet_tag(address_elem.text),
                              address_elem.sourceline)
                              
            inet_list = unit_elem.xpath("family/inet")
            if inet_list:
                inet_elem = inet_list[0]
                tag_addresses(inet_elem)
                t = taglib.tag("IP version", "IPv4")
                t.implied_by(unit_tag, inet_elem.sourceline)
                
            inet6_list = unit_elem.xpath("family/inet6")
            if inet6_list:
                inet6_elem = inet6_list[0]
                tag_addresses(inet6_elem)
                t = taglib.tag("IP version", "IPv6")
                t.implied_by(unit_tag, inet6_elem.sourceline)
                

def tag_protocols(top):
    
    protocol = "BGP"
    routing_options_local_as_list = top.xpath("routing-options/autonomous-system/as-number")
    routing_options_router_id_list = top.xpath("routing-options/router-id")
    
    protocol_elem_list = top.xpath("protocols/%s" % protocol.lower())
    if protocol_elem_list:
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for group_elem in protocol_elem.xpath("group"):
            name_elem = group_elem.xpath("name")[0]
            group_tag = taglib.tag("%s group" % protocol,
                                   "%s %s" % (device_tag.name, name_elem.text))
            group_tag.implied_by(device_tag, name_elem.sourceline)
            for peer_name_elem in group_elem.xpath("neighbor/name"): 
                local_address_elem_list = peer_name_elem.xpath("ancestor::*/local-address")
                if local_address_elem_list:
                    local_address_elem = local_address_elem_list[0]
                elif routing_options_router_id_list:
                    local_address_elem = routing_options_router_id_list[0]
                
                local_elem_list = peer_name_elem.xpath("ancestor::*/local-as/as-number")
                if local_elem_list:
                    local_elem = local_elem_list[0]
                elif routing_options_local_as_list:
                    local_elem = routing_options_local_as_list[0]
                
                if local_elem is not None:
                    localasn_tag = taglib.as_number_tag(local_elem.text, "local AS")
                    
                    localasn_tag.implies(taglib.as_number_tag(local_elem.text),
                                         local_elem.sourceline)
                 
                asn_elem_list = peer_name_elem.xpath("ancestor::*/peer-as")
                if asn_elem_list:
                    asn_elem = asn_elem_list[0]
                else:
                    asn_elem = local_elem
                    
                asn_tag = taglib.as_number_tag(asn_elem.text, kind="remote AS")
                asn_tag.implies(taglib.as_number_tag(asn_elem.text),
                                asn_elem.sourceline)
                
                if asn_elem.text == local_elem.text:
                    peering_relationship = "iBGP"
                else:
                    peering_relationship = "eBGP"
                
                address_tag = taglib.ip_address_tag(peer_name_elem.text)
                peering_tag = taglib.tag("%s peering" % peering_relationship,
                                         "%s %s" % (device_tag.name, peer_name_elem.text),
                                         sort_name="%s %s" % (device_tag.name, address_tag.sort_name))
                peering_tag.implies(protocol_tag, peer_name_elem.sourceline)
                peering_tag.implied_by(device_tag, peer_name_elem.sourceline)
                peering_tag.implied_by(group_tag, peer_name_elem.sourceline)
                
                asn_tag.implied_by(peering_tag, asn_elem.sourceline)
                localasn_tag.implied_by(peering_tag, local_elem.sourceline)

                peer_tag = taglib.ip_address_tag(peer_name_elem.text, kind="%s peer" % protocol)
                peer_tag.implies(address_tag, peer_name_elem.sourceline)
                
                if local_address_elem is not None:
                    peer2_tag = taglib.ip_address_tag(local_address_elem.text, kind="%s peer" % protocol.upper())
                    address2_tag = taglib.ip_address_tag(local_address_elem.text)
                    peer2_tag.implies(address2_tag, local_address_elem.sourceline)
                    local_peer_tag = taglib.ip_address_tag(local_address_elem.text,
                                                           kind="local %s peer" % protocol)
                    local_peer_tag.implied_by(peering_tag, local_address_elem.sourceline)
                    local_peer_tag.implies(peer2_tag, peer_name_elem.sourceline)
                
                remote_peer_tag = taglib.ip_address_tag(peer_name_elem.text,
                                                          kind="remote %s peer" % protocol)
                remote_peer_tag.implied_by(peering_tag, peer_name_elem.sourceline)
                remote_peer_tag.implies(peer_tag, peer_name_elem.sourceline)
                
        
    protocol = "MSDP"
    protocol_elem_list = top.xpath("protocols/%s" % protocol.lower())
    if protocol_elem_list:
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for group_elem in protocol_elem.xpath("group"):
            name_elem = group_elem.xpath("name")[0]
            group_tag = taglib.tag("%s group" % protocol,
                                   "%s %s" % (device_tag.name, name_elem.text))
            group_tag.implied_by(device_tag, name_elem.sourceline)
            for peer_name_elem in group_elem.xpath("peer/name"):
                peer_tag = taglib.tag("%s peer" % protocol, peer_name_elem.text)
                address_tag = taglib.ip_address_tag(peer_name_elem.text)
                peer_tag.implies(address_tag, peer_name_elem.sourceline)
                peer_tag.implied_by(group_tag, peer_name_elem.sourceline)
                peer_tag.implies(protocol_tag, peer_name_elem.sourceline)

    ospf_version_dict = {'ospf':'OSPF', 'ospf3':'OSPFv3'}
    for protocol_key, protocol in ospf_version_dict.items():
        protocol_elem_list = top.xpath("protocols/%s" % protocol_key)
        if not protocol_elem_list:
            continue
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for area_elem in protocol_elem.xpath("area"):
            name_elem = area_elem.xpath("name")[0]
            area_tag = taglib.tag("%s area" % protocol, name_elem.text)
            area_tag.implies(protocol_tag, name_elem.sourceline)
            for interface_name_elem in area_elem.xpath("interface/name"):
                if interface_name_elem.text == "all":
                    interface_tags = all_interface_tags
                else:
                    interface_tags = [
                        taglib.tag("interface", 
                                   "%s %s" % (device_tag.name, 
                                              interface_name_elem.text))]
                for t in interface_tags:
                    t.implies(area_tag, interface_name_elem.sourceline)

    protocol = "PIM"
    protocol_elem_list = top.xpath("protocols/%s" % protocol.lower())
    if protocol_elem_list:
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for interface_name_elem in protocol_elem.xpath("interface/name"):
            if interface_name_elem.text == "all":
                interface_tags = all_interface_tags
            else:
                interface_tags = [
                    taglib.tag("interface", 
                               "%s %s" % (device_tag.name, 
                                          interface_name_elem.text))]
            for t in interface_tags:
                t.implies(protocol_tag, interface_name_elem.sourceline)

    for protocol in ("RIP", "RIPng"):
        protocol_elem_list = top.xpath("protocols/%s" % protocol.lower())
        if not protocol_elem_list:
            continue
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for group_elem in protocol_elem.xpath("group"):
            name_elem = group_elem.xpath("name")[0]
            group_tag = taglib.tag("%s group" % protocol,name_elem.text)
            group_tag.implies(protocol_tag, name_elem.sourceline)
            for interface_name_elem in group_elem.xpath("neighbor/name"):
                if interface_name_elem.text == "all":
                    interface_tags = all_interface_tags
                else:
                    interface_tags = [
                        taglib.tag("interface", 
                                   "%s %s" % (device_tag.name, 
                                              interface_name_elem.text))]
                for t in interface_tags:
                    t.implies(group_tag, interface_name_elem.sourceline)

    protocol = "router-advertisement"
    protocol_elem_list = top.xpath("protocols/%s" % protocol.lower())
    if protocol_elem_list:
        protocol_elem = protocol_elem_list[0]
        protocol_tag = taglib.tag("routing protocol", protocol)
        protocol_tag.used(protocol_elem.sourceline)
        for interface_elem in protocol_elem.xpath("interface"):
            interface_name_elem = interface_elem.xpath("name")[0]
            if interface_name_elem.text == "all":
                interface_tags = all_interface_tags
            else:
                interface_tags = [
                    taglib.tag("interface", 
                               "%s %s" % (device_tag.name, 
                                          interface_name_elem.text))]
            for t in interface_tags:
                ratag = taglib.tag("ND router advertisement server", 
                                    "%s %s" % (device_tag.name, interface_name_elem.text))
                ratag.implied_by(t, interface_name_elem.sourceline);
                
                for prefix_name_elem in interface_elem.xpath("prefix/name"):
                    ratag.implies(taglib.ip_subnet_tag(prefix_name_elem.text),
                                    prefix_name_elem.sourceline)
                    

def tag_location(top):
    for prop in top.xpath("system/location/*"):
        t = taglib.tag("location %s" % prop.tag, prop.text)
        t.used(prop.sourceline)

def tag_scripts(top):
    for script_type in ("commit", "event", "op"):
        for cs in top.xpath("system/scripts/%s/file" % script_type):
            file_elem = cs.xpath("name")[0]
            t = taglib.tag("%s script" % script_type, "%s %s" % (device_tag.name,file_elem.text))
            t.implies(device_tag, file_elem.sourceline)
            tf = taglib.tag("%s script file" % script_type, file_elem.text)
            tf.implied_by(t, file_elem.sourceline)
            source_elems = cs.xpath("source")
            if source_elems:
                elem = source_elems[0]
                src = taglib.tag("%s script source" % script_type, elem.text)
                src.implied_by(t, elem.sourceline)
                    

def tag_matches(top, path, kind, context):
    for e in top.xpath(path):
        t = taglib.tag(kind, e.text)
        t.implied_by(context, e.sourceline)


def main():
    filename = taglib.default_filename
    with file(filename) as f:
        tree = etree.parse(f)
    top = tree.getroot()[0]

    nsmap = top.nsmap
    if None in nsmap:
        nsmap['x'] = nsmap[None]
        del nsmap[None]
    
    context = taglib.env_tags.device
    tag_matches(top, "system/domain-name", "domain name", context)
    tag_matches(top, "system/time-zone", "time zone", context)
    tag_matches(top, "system/name-server/name", "name server", context)
    tag_matches(top, "system/radius-server/name", "RADIUS server", context)
    tag_matches(top, "system/tacplus-server/name", "TACACS+ server", context)
    tag_matches(top, "system/ntp/boot-server", "NTP boot server", context)
    tag_matches(top, "system/ntp/server/name", "NTP server", context)
    tag_matches(top, "system/login/user/name", "user", context)
    tag_matches(top, "snmp/community/name", "SNMP community", context)
        
    tag_services(top)
    tag_interfaces(top)
    tag_protocols(top)
    tag_location(top)
    tag_scripts(top)
    
    taglib.output_tagging_log()

if __name__ == '__main__':
    main()
