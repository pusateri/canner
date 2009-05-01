#!/usr/bin/env python

#
# Copyright 2007-2008 !j Incorporated
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

import pygments
import pygments.formatters
from pygments.formatter import Formatter
import pygments.lexers
from pygments.token import *
from canner import taglib
import sys
import traceback
import IPy; IPy.check_addr_prefixlen = False
import os
import re

EndOfCommand = Token.EndOfCommand
ssidDict = {}
ssidLineDict = {}
ssidsForInterface = {}
if_addrs4 = {}
if_addrs6 = {}
peer_groups = {}
peer_dicts = {}
ipv6_general_prefixes = {}
device_tag = taglib.env_tags.device
ipv6_addresses = False
ipv6_unicast_routing = None

class UnexpectedToken(Exception):
    pass

class TagsFormatter(Formatter):
    """
    FIXME: help should go here
    """
    name = 'Tag Formatter'
    aliases = ['tags']
    filenames = ['*.tags']


    def format(self, tokenSource, outFile):
        self.tokenSource = self.wrapSource(tokenSource)
        self.outFile = outFile
        self.lineNum = 1
        self.fileName = self.options.get('fn', '?')
        self.tagFormat = "%s:%%d: %%s %%s\n" % self.fileName
        self.sshEnabled = False

        try:
            self.getNextToken()
            self.accept(Generic.Output)
            self.command()
        except StopIteration:
            pass


    def wrapSource(self, tokenSource):
        for ttype, value in tokenSource:
            if ttype not in Text or ttype in Whitespace:
                yield ttype, value
            else:
                stripped = value.strip()
                if stripped:
                    yield ttype, stripped
            if ttype in Text and '\n' in value:
                yield EndOfCommand, ''
            self.lineNum += value.count('\n')

    def getNextToken(self):
        self.tokenType, self.tokenValue = self.tokenSource.next()


    def accept(self, tokenType):
        if self.tokenType in tokenType:
            value = self.tokenValue
            self.getNextToken()
            return value
        return None

    def expect(self, tokenType):
        value = self.accept(tokenType)
        if value is None:
            msg = 'expected %s, got %s %s' % (
                tokenType, self.tokenType, repr(self.tokenValue))
            fn, ln, fn, txt = traceback.extract_stack(limit=2)[0]
            sys.stderr.write('error: %s:%d: %s (\'%s\' line %d)\n' % (
                self.fileName, self.lineNum, msg, fn, ln))
            raise UnexpectedToken(msg)
        return value

    def skip(self, *tokenTypes):
        while any(t for t in tokenTypes if self.tokenType in t):
            self.getNextToken()

    def skipTo(self, tokenType):
        while self.tokenType not in tokenType:
            self.getNextToken()
        return self.accept(tokenType)


    def command(self):
        while True:
            try:
                if self.accept(Whitespace) is not None:
                    self.skipTo(EndOfCommand)
                    continue
                self.skip(Comment, EndOfCommand)
                op = self.accept(Operator)
                if op == 'no':
                    self.skipTo(EndOfCommand)
                    continue
                cmd = self.expect(Keyword)
                if False:  # just so all the real options can use elif...
                    pass

                elif cmd == 'dot11':
                    self.dot11()

                elif cmd == 'hostname':
                    t = taglib.tag("hostname", self.accept(String))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    self.expect(EndOfCommand)

                elif cmd == 'interface':
                    self.interface()

                elif cmd == 'ip':
                    self.ip()

                elif cmd == "ipv6":
                    self.ip(version="IPv6")
                    
                elif cmd == "ntp":
                    self.ntp()

                elif cmd == 'radius-server':
                    self.radius()

                elif cmd == 'router':
                    self.router()

                elif cmd == "snmp-server":
                    self.snmp_server()

                elif cmd == 'tacacs-server':
                    self.tacacs_server()
                    
                elif cmd == 'username':
                    t = taglib.tag("user", self.accept(String))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    self.skipTo(EndOfCommand)

                # elif cmd == 'version':
                #     self.outputTag("version--" + self.accept(String))
                #     self.expect(EndOfCommand)

                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)
                
        if ipv6_addresses and ipv6_unicast_routing is None:
            t = taglib.tag("forwarding disabled", "IPv6 unicast")
            t.implied_by(device_tag, ipv6_unicast_routing)
    
    
    def dot11(self):
        subcmd = self.expect(Keyword)
        if subcmd == 'ssid':
            ssid = self.accept(String)
            self.expect(EndOfCommand)
            
            while True:
                if self.accept(Whitespace) is None:
                    return
                
                try:
                    op = self.accept(Operator)
                    cmd = self.expect(Keyword)
                    
                    if False:
                        pass
                        
                    elif cmd == "vlan":
                        vlan_id = self.expect(Literal)
                        ssidDict[vlan_id] = ssid
                        ssidLineDict[vlan_id] = self.lineNum
                        t = taglib.tag("VLAN ID", vlan_id, sort_name="%05d" % int(vlan_id))
                        t.used(self.lineNum)
                        self.expect(EndOfCommand)
                        
                    else:
                        self.skipTo(EndOfCommand)
                        
                except UnexpectedToken:
                    self.skipTo(EndOfCommand)
        else:
            self.skipTo(EndOfCommand)  
        
    def interface(self):
        ra_list = []        
        name = self.expect(Name)
   
        # TODO: make interface names sort in ascending numeric order
        if_tag = taglib.tag("interface", 
                            "%s %s" % (taglib.env_tags.device.name, name))
        if_tag.implied_by(taglib.env_tags.snapshot, self.lineNum)
        if_tag.implies(taglib.env_tags.device, self.lineNum)
        if_tag.implies(taglib.tag("interface type", 
                                  re.sub(r"[0-9/.]+$", "", name)),
                       self.lineNum)
        
        m = re.match(r"(Dot11Radio[0-9]+)(\.)?([0-9]+)?$", name)
        if m:
            if not m.group(2):
                ssidsForInterface[m.group(1)] = []
                if_tag.implies(taglib.tag("interface type", "wireless"), self.lineNum)
                
            if m.group(3):
                t = taglib.tag("VLAN ID", m.group(3), sort_name="%05d" % int(m.group(3)))
                t.implied_by(if_tag, self.lineNum)
                if ssidDict[m.group(3)] in ssidsForInterface[m.group(1)]:
                    t = taglib.tag("SSID", ssidDict[m.group(3)])
                    t.implied_by(if_tag, ssidLineDict[m.group(3)])
        
        self.expect(EndOfCommand)
        while True:
            
            if self.accept(Whitespace) is None:
                ra_suppress = False
                ra_prefix_line = None
                ra_if_prefix_line = None
                ra_prefix = []
                if_prefix = []
                # (ra_suppress, ra_line, if_prefix, ra_prefix)
                for ra in ra_list:
                    ra_suppress |= ra[0]
                    if ra[0]:
                        admin = taglib.tag("admin disabled", "ND router advertisement server")
                        admin.implied_by(if_tag, ra[1])
                    if len(ra[2]):
                        if_prefix = ra[2]
                        ra_if_prefix_line = ra[1]
                    if len(ra[3]):
                        ra_prefix = intra[3]
                        ra_prefix_line = ra[1]
                
                if ra_prefix_line or ra_if_prefix_line:
                    if not ra_suppress:
                        rp = taglib.tag("routing protocol", "router advertisement")
                        if ra_if_prefix_line:
                            rp.used(ra_if_prefix_line)
                        elif ra_prefix_line:
                            rp.used(ra_prefix_line)
                    ratag = taglib.tag("ND router advertisement server", if_tag.name)
                    if len(ra_prefix):
                        for p in ra_prefix:
                            ratag.implies(taglib.ip_subnet_tag(p), ra_prefix_line)
                    else:
                        for p in if_prefix:
                            ratag.implies(taglib.ip_subnet_tag(p), ra_if_prefix_line)
                return

            if self.accept(Comment) is not None:
                self.skipTo(EndOfCommand)
                continue
                
            try:
                op = self.accept(Operator)
                cmd = self.expect(Keyword)

                if False:
                    pass

                elif cmd == "description":
                    description = self.expect(String)
                    t = taglib.tag("interface description", description)
                    t.implied_by(if_tag, self.lineNum)
                    self.expect(EndOfCommand)

                elif cmd == "ip":
                    self.ip(if_tag=if_tag, if_name=name, version="IPv4")

                elif cmd == "ipv6":
                    ra_list.append(self.ip(if_tag=if_tag, if_name=name, version="IPv6"))
                                        
                elif cmd == "ssid":
                    if m and not m.group(2):
                        ssidsForInterface[m.group(1)].append(self.expect(Literal))
                    self.expect(EndOfCommand)
                
                elif cmd == "tunnel":
                    self.skipTo(EndOfCommand)
                    
                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)
        
    
    def radius(self):
        cmd = self.expect(Keyword)

        if cmd == "host":
            t = taglib.tag("RADIUS server", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
        
        self.skipTo(EndOfCommand)
        
    def router(self):
        protocol = self.expect(Keyword)
        protocol_tag = taglib.tag("routing protocol", protocol.upper())
        protocol_tag.implied_by(taglib.env_tags.device, self.lineNum)
        
        if protocol == "bgp":
            bgp_router_id = None
            bgp_router_id_lineNum = None
            local_as = self.expect(Literal)
            local_as_tag = taglib.as_number_tag(local_as, "local AS")
            local_as_lineNum = self.lineNum
            local_as_tag.implies(taglib.as_number_tag(local_as), local_as_lineNum)
            
            self.skipTo(EndOfCommand)
            while True:
                disable = False
                
                if self.accept(Whitespace) is None:
                    for peer, peerdict in peer_dicts.items():
                        bgp_local_addr = None
                        bgp_local_addr_lineNum = None
                        peer_lineNum = peerdict.get("peer_lineNum", None)
                        
                        peer_group = peerdict.get("peer_group", None)
                        if peer_group:
                            peer_group_dict = peer_groups.get(peer_group, None)
                        else:
                            peer_group_dict = None
                            
                        peer_as = peerdict.get("peer_as", None)
                        if peer_as is not None:
                            peer_as_lineNum = peerdict.get("peer_as_lineNum", None)
                        elif peer_group_dict:
                            peer_as = peer_group_dict.get("peer_as", None);
                            peer_as_lineNum = peer_group_dict.get("peer_as_lineNum", None)
                            
                        if peer_as is None:
                            continue

                        update_source = peerdict.get("update_source", None)
                        update_source_lineNum = peerdict.get("update_source_lineNum", None)
                        if update_source is None and peer_group_dict is not None:
                            update_source = peer_group_dict.get("update_source", None)
                            update_source_lineNum = peer_group_dict.get("update_source_lineNum", None)
                            
                        peer_ip = IPy.IP(peer)
                        if update_source is None:
                            if peer_ip.version() == 4 and bgp_router_id:
                                bgp_local_addr = bgp_router_id
                                bgp_local_addr_lineNum = bgp_router_id_lineNum
                            else:
                                update_source = 'Loopback0'
                                update_source_lineNum = 0
                            
                        if update_source is not None:
                            bgp_local_addr_lineNum = update_source_lineNum
                            if peer_ip.version() == 4:
                                bgp_local_addr = if_addrs4.get(update_source)
                            elif peer_ip.version() == 6:
                                bgp_local_addr = if_addrs6.get(update_source)
                        
                        peer_tag = taglib.ip_address_tag(peer, kind="%s peer" % protocol.upper())
                        
                        address_tag = taglib.ip_address_tag(peer)
                        peer_tag.implies(address_tag, peer_lineNum)
                        
                        peer_as_tag = taglib.as_number_tag(peer_as, "remote AS")
                        peer_as_tag.implies(taglib.as_number_tag(peer_as), peer_as_lineNum)
                        
                        if peer_as == local_as:
                            peering_relationship = "iBGP"
                        else:
                            peering_relationship = "eBGP"

                        peering_tag = taglib.tag("%s peering" % peering_relationship,
                                                 "%s %s" % (device_tag.name, peer),
                                                 sort_name="%s %s" % (device_tag.name, peer_tag.sort_name))
                        peering_tag.implies(protocol_tag, peer_lineNum)
                        peering_tag.implied_by(device_tag, peer_lineNum)
                        local_as_tag.implied_by(peering_tag, peer_lineNum)
                        peer_as_tag.implied_by(peering_tag, peer_lineNum)
                        
                        if bgp_local_addr is not None:
                            peer2_tag = taglib.ip_address_tag(bgp_local_addr, kind="%s peer" % protocol.upper())
                            address2_tag = taglib.ip_address_tag(bgp_local_addr)
                            peer2_tag.implies(address2_tag, bgp_local_addr_lineNum)
                            local_peer_tag = taglib.ip_address_tag(bgp_local_addr, kind="local %s peer" % protocol.upper())
                            local_peer_tag.implied_by(peering_tag, bgp_local_addr_lineNum)
                            local_peer_tag.implies(peer2_tag, bgp_local_addr_lineNum)
                            
                        remote_peer_tag = taglib.ip_address_tag(peer, kind="remote %s peer" % protocol.upper())
                        remote_peer_tag.implied_by(peering_tag, peer_lineNum)
                        remote_peer_tag.implies(peer_tag, peer_lineNum)

                    return

                if self.accept(Comment) is not None:
                    self.skipTo(EndOfCommand)
                    continue
                
                try:
                    op = self.accept(Operator)
                    if op and op == "no":
                        disable = True
                        
                    cmd = self.expect(Keyword)

                    if cmd == "neighbor":
                        peer_group = None
                        peer = self.accept(Number)
                        if peer is None:
                            # if no address, then its probably a peer group
                            peer_group = self.expect(String)
                            peerdict = peer_groups.get(peer_group, None)
                            if peerdict is None:
                                peerdict = {}
                                peer_groups[peer_group] = peerdict
                        else:
                            peerdict = peer_dicts.get(peer, None)
                            if peerdict is None:
                                peerdict = {}
                                peerdict["peer"] = peer
                                peerdict["peer_lineNum"] = self.lineNum
                                peerdict["disable"] = disable
                                peer_dicts[peer] = peerdict
                            
                        subcmd = self.expect(Keyword)
                        if subcmd == "remote-as":
                            peerdict["peer_as"] = self.expect(Literal)
                            peerdict["peer_as_lineNum"] = self.lineNum
                            
                        elif subcmd == "peer-group":
                            if peer is not None:
                                peerdict["peer_group"] = self.accept(Literal)
                            
                        elif subcmd == "update-source":
                            peerdict["update_source"] = self.expect(Literal)
                            peerdict["update_source_lineNum"] = self.lineNum
                            
                    
                    elif cmd == "bgp":
                        subcmd = self.expect(Keyword)
                        if subcmd == "router-id":
                            bgp_router_id = self.accept(Literal)
                            bgp_router_id_lineNum = self.lineNum
                        else:
                            self.skipTo(EndOfCommand)
                    
                    elif cmd == "router-id":
                        bgp_router_id = self.accept(Literal)
                        bgp_router_id_lineNum = self.lineNum

                    self.skipTo(EndOfCommand)

                except UnexpectedToken:
                    self.skipTo(EndOfCommand)
                    
        self.skipTo(EndOfCommand)

    def snmp_server(self):
        cmd = self.expect(Keyword)

        if cmd == "community":
            t = taglib.tag("SNMP community", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
        
        self.skipTo(EndOfCommand)

    def tacacs_server(self):
        cmd = self.expect(Keyword)

        if cmd == 'host':
            t = taglib.tag("TACACS+ server", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)

        else:
            self.skipTo(EndOfCommand)

    def ntp(self):
        cmd = self.expect(Keyword)

        if cmd == "server":
            t = taglib.tag("NTP server", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)

        self.skipTo(EndOfCommand)


    def ip(self, if_tag=None, if_name=None, version=None):
        ra_line = None
        ra_suppress = False
        ra_prefix = []
        if_prefix = []
        cmd = self.expect(Keyword)

        if False:
            pass

        elif cmd == 'address':
            name = self.accept(String)
            ipaddress = self.accept(Literal)
            if ipaddress:
                self.accept(Punctuation)    # allow detection of address/prefix length
                if name:
                    ipaddress = IPy.intToIp(IPy.IP(ipaddress).int() | ipv6_general_prefixes[name].int(), 6)
                address = ipaddress + "/" + self.expect(Literal)
                if if_name:
                    if version == 'IPv4':
                        if_addrs4.setdefault(if_name, ipaddress)
                    elif version == 'IPv6':
                        if_addrs6.setdefault(if_name, ipaddress)
                ifaddr_tag = taglib.ip_address_tag(address, 
                                                   kind="interface address")
                address_tag = taglib.ip_address_tag(address)
                subnet_tag = taglib.ip_subnet_tag(address)
                ifaddr_tag.implied_by(if_tag, self.lineNum)
                address_tag.implied_by(ifaddr_tag, self.lineNum)
                subnet_tag.implied_by(address_tag, self.lineNum)
                if version:
                    version_tag = taglib.tag("IP version", version)
                    version_tag.implied_by(if_tag, self.lineNum)
                    
                    # add router advertisement by default on multi-access networks
                    if version == 'IPv6':
                        ipv6_addresses = True
                        if re.search(r"eth|fddi|port-channel", if_tag.name, re.I):
                            if_prefix.append(subnet_tag.name)
                            ra_line = self.lineNum
                    
            self.skipTo(EndOfCommand)

        elif cmd == 'cef':
            if not version:
                version = "IPv4"
            distributed = self.accept(Keyword)
            if distributed == "distributed":
                cef = " ".join((version, distributed))
            else:
                cef = version
            t = taglib.tag("Cisco express forwarding", cef)
            t.implied_by(device_tag, self.lineNum)
            self.skipTo(EndOfCommand)
        
        elif cmd == 'domain name' or cmd == 'domain-name':
            t = taglib.tag("domain name", self.expect(String))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)

        elif cmd == 'general-prefix':
            name = self.expect(String)
            ipaddress = self.expect(Literal)
            self.expect(Punctuation)
            address = ipaddress + "/" + self.expect(Literal)
            ipv6_general_prefixes[name] = IPy.IP(address)
            self.expect(EndOfCommand)
            
        elif cmd == 'helper-address':
            t = taglib.tag("BOOTP relay", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)
            
        elif cmd == 'http':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'server':
                t = taglib.tag("service", "HTTP")
                t.implied_by(taglib.env_tags.device, self.lineNum)
            elif nextCmd == 'secure-server':
                t = taglib.tag("service", "HTTPS")
                t.implied_by(taglib.env_tags.device, self.lineNum)
            self.skipTo(EndOfCommand)

        elif cmd == 'name-server':
            t = taglib.tag("name server", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)
        
        elif cmd == 'nd':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'prefix':
                ra_line = self.lineNum
                nd_prefix = None
                default_prefix = self.accept(Keyword)
                if not default_prefix:
                    nd_prefix = self.expect(Literal) + self.expect(Punctuation) + self.expect(Literal)
                keyword = self.accept(Keyword)
                if keyword is None or not 'no-ad' in keyword:
                    if nd_prefix:
                        ra_prefix.append(nd_prefix)
            elif nextCmd == 'suppress-ra':
                ra_line = self.lineNum
                ra_suppress = True
            self.skipTo(EndOfCommand)
        
        elif cmd == 'scp':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'server':
                nextCmd = self.expect(Keyword)
                if nextCmd == 'enable':
                    t = taglib.tag("service", taglib.protocol_name(cmd))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
            self.skipTo(EndOfCommand)

        elif cmd == 'ssh':
            if self.sshEnabled == False:
                t = taglib.tag("service", taglib.protocol_name(cmd))
                t.implied_by(taglib.env_tags.device, self.lineNum)
                self.sshEnabled = True
            nextCmd = self.expect(Keyword)
            if nextCmd == 'version':
                version = self.expect(Literal)
                if version == '2':
                    t = taglib.tag("service", taglib.protocol_name(cmd))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    t = taglib.tag("service", "SSHv2")
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                elif version == '1':
                    t = taglib.tag("service", taglib.protocol_name(cmd))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    t = taglib.tag("service", "SSHv1")
                    t.implied_by(taglib.env_tags.device, self.lineNum)
            self.skipTo(EndOfCommand)


        elif cmd == 'unicast-routing':
            ipv6_unicast_routing = self.lineNum
            self.expect(EndOfCommand)
            
        else:
            self.skipTo(EndOfCommand)
        return (ra_suppress, ra_line, if_prefix, ra_prefix)

def main():
    filename = taglib.default_filename
    content = open(filename).read()

    lexer = pygments.lexers.get_lexer_by_name("ios")
    formatter = TagsFormatter(fn=filename)

    pygments.highlight(content, lexer, formatter, sys.stdout)
        
    taglib.output_tagging_log()


if __name__ == '__main__':
    main()
