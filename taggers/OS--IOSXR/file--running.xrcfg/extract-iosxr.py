#!/usr/bin/env python

#
# Copyright 2008 !j Incorporated
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
ipv6_general_prefixes = {}
bgp_group_remote_as = {}
bgp_group_remote_as_lineNum = {}
bgp_group_local_as = {}
bgp_group_local_as_lineNum = {}
device_tag = taglib.env_tags.device

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

                elif cmd == 'domain':
                    self.domain()
                    
                elif cmd == 'hostname':
                    t = taglib.tag("hostname", self.accept(String))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    self.expect(EndOfCommand)

                elif cmd == 'interface':
                    self.interface()
                    
                elif cmd == "ntp":
                    self.ntp()

                elif cmd == 'radius-server':
                    self.radius()

                elif cmd == 'router':
                    self.router()

                elif cmd == "snmp-server":
                    self.snmp_server()
                    
                elif cmd == "ssh":
                    self.ssh()
                    
                elif cmd == "tacacs-server":
                    self.tacacs_server()

                elif cmd == 'username':
                    t = taglib.tag("user", self.accept(String))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    self.skipTo(EndOfCommand)

                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)

    def interface(self):
        # preconfigure is inserted into the config before the interface name when the matching
        # hardware isn't found. for now, lets just ignore these interfaces.
        inactive = self.accept(Keyword)
        name = self.expect(Name)
        if_tag = None
        
        if not inactive:
            if_tag = taglib.tag("interface", 
                                "%s %s" % (taglib.env_tags.device.name, name))
            if_tag.implied_by(taglib.env_tags.snapshot, self.lineNum)
            if_tag.implies(taglib.env_tags.device, self.lineNum)
            if_tag.implies(taglib.tag("interface type", 
                                      re.sub(r"[0-9/.]+$", "", name)),
                           self.lineNum)
                
        self.expect(EndOfCommand)
        while True:
            
            if self.accept(Whitespace) is None:
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
                    if not inactive:
                        t = taglib.tag("interface description", description)
                        t.implied_by(if_tag, self.lineNum)
                    self.expect(EndOfCommand)
                    
                elif cmd == "ipv4":
                    self.ip(if_tag=if_tag, version="IPv4", active=not inactive)

                elif cmd == "ipv6":
                    ra = self.ip(if_tag=if_tag, version="IPv6", active=not inactive)
                    # (ra_suppress, ra_line, if_prefix, ra_prefix)
                    if not ra[0] and ra[1]:
                        ratag = taglib.tag("ra server", if_tag.name)
                        if len(ra[3]):
                            for p in ra[3]:
                                ratag.implies(taglib.ip_subnet_tag(p), ra[1])
                        else:
                            for p in ra[2]:
                                ratag.implies(taglib.ip_subnet_tag(p), ra[1])
                
                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)
                
    
    def domain(self):
        cmd = self.expect(Keyword)

        if cmd == "name":
            t = taglib.tag("domain name", self.expect(String))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)
            
        elif cmd == 'name-server':
            t = taglib.tag("name server", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
            self.expect(EndOfCommand)
            
        else:
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
            local_as = self.expect(Literal)
            local_as_tag = taglib.as_number_tag(local_as, "local AS")
            local_as_lineNum = self.lineNum
            local_as_tag.implies(taglib.as_number_tag(local_as), local_as_lineNum)

            self.skipTo(EndOfCommand)
            while True:
            
                if self.accept(Token.EndOfMode) is not None:
                    return

                if self.accept(Whitespace) is not None:
                    continue
                    
                if self.accept(Comment) is not None:
                    self.skipTo(EndOfCommand)
                    continue
                
                try:
                    op = self.accept(Operator)
                    if op:
                        pass
                        
                    cmd = self.expect(Keyword)

                    if False:
                        pass

                    elif cmd == "neighbor-group":
                        self.bgp_neighbor_group(self.expect(Literal))
                    
                    elif cmd == "neighbor":
                        peer = self.expect(Literal)
                        peer_tag = taglib.ip_address_tag(peer, kind="%s peer" % protocol.upper())
                        peer_lineNum = self.lineNum
                        address_tag = taglib.ip_address_tag(peer)
                        peer_tag.implies(address_tag, self.lineNum)
                        
                        self.expect(EndOfCommand)
                        self.bgp_neighbor(protocol_tag, peer, peer_tag, peer_lineNum, local_as, local_as_tag, local_as_lineNum)
                        
                    else:
                        self.skipTo(EndOfCommand)

                except UnexpectedToken:
                    self.skipTo(EndOfCommand)
                    
        self.skipTo(EndOfCommand)
    
    def bgp_neighbor(self, protocol_tag, peer, peer_tag, peer_lineNum, top_local_as, top_local_as_tag, top_local_as_lineNum):
        local_as = top_local_as
        local_as_tag = top_local_as_tag
        local_as_lineNum = top_local_as_lineNum
        
        while True:
        
            if self.accept(Token.EndOfMode) is not None:
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
                                
                remote_peer_tag = taglib.ip_address_tag(peer, kind="remote %s peer" % protocol_tag.name)
                remote_peer_tag.implied_by(peering_tag, peer_lineNum)
                remote_peer_tag.implies(peer_tag, peer_lineNum)
                return

            if self.accept(Whitespace) is not None:
                continue
                    
            if self.accept(Comment) is not None:
                self.skipTo(EndOfCommand)
                continue
            
            try:
                op = self.accept(Operator)
                if op:
                    pass
                    
                cmd = self.expect(Keyword)

                if False:
                    pass
                
                elif cmd == "local-as":
                    local_as = self.expect(Literal)
                    local_as_lineNum = self.lineNum
                    local_as_tag = taglib.as_number_tag(local_as, "local AS")
                    local_as_tag.implies(taglib.as_number_tag(local_as), local_as_lineNum)
                    self.expect(EndOfCommand)
                    
                elif cmd == "remote-as":
                    peer_as = self.expect(Literal)
                    peer_as_lineNum = self.lineNum
                    peer_as_tag = taglib.as_number_tag(peer_as, "remote AS")
                    peer_as_tag.implies(taglib.as_number_tag(peer_as), peer_as_lineNum)
                    self.expect(EndOfCommand)
                    
                elif cmd == "use":
                    subcmd = self.expect(Keyword)
                    if subcmd == "neighbor-group":
                        group = self.expect(Literal)
                        group_local_as = bgp_group_local_as.get(group, None)
                        if group_local_as is not None:
                            local_as = group_local_as
                            local_as_lineNum = bgp_group_local_as_lineNum.get(group, None)
                            local_as_tag = taglib.as_number_tag(local_as, "local AS")
                            local_as_tag.implies(taglib.as_number_tag(local_as), local_as_lineNum)
                        
                        group_peer_as = bgp_group_remote_as.get(group, None)
                        if group_peer_as is not None:
                            peer_as = group_peer_as
                            peer_as_lineNum = bgp_group_remote_as_lineNum.get(group, None)
                            peer_as_tag = taglib.as_number_tag(peer_as, "remote AS")
                            peer_as_tag.implies(taglib.as_number_tag(peer_as), peer_as_lineNum)
                        
                    self.skipTo(EndOfCommand)
                    
                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)
                                
    
    def bgp_neighbor_group(self, group):
        self.expect(EndOfCommand)
        while True:

            if self.accept(Token.EndOfMode) is not None:
                return

            if self.accept(Whitespace) is not None:
                continue
                
            if self.accept(Comment) is not None:
                self.skipTo(EndOfCommand)
                continue

            try:
                op = self.accept(Operator)
                if op:
                    pass

                cmd = self.expect(Keyword)

                if False:
                    pass

                elif cmd == "local-as":
                    bgp_group_local_as[group] = self.expect(Literal)
                    bgp_group_local_as_lineNum[group] = self.lineNum
                    self.expect(EndOfCommand)
                    
                elif cmd == "remote-as":
                    bgp_group_remote_as[group] = self.expect(Literal)
                    bgp_group_remote_as_lineNum[group] = self.lineNum
                    self.expect(EndOfCommand)
                    
                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)
        
    def snmp_server(self):
        cmd = self.expect(Keyword)

        if cmd == "community":
            t = taglib.tag("SNMP community", self.expect(Literal))
            t.implied_by(taglib.env_tags.device, self.lineNum)
        
        self.skipTo(EndOfCommand)

    def ntp(self):
        self.expect(EndOfCommand)
        
        while True:
            
            if self.accept(Whitespace) is None:
                return

            if self.accept(Comment) is not None:
                self.skipTo(EndOfCommand)
                continue
                
            try:
                cmd = self.expect(Keyword)

                if False:
                    pass

                elif cmd == "server":
                    t = taglib.tag("NTP server", self.expect(Literal))
                    t.implied_by(taglib.env_tags.device, self.lineNum)
                    self.expect(EndOfCommand)
                                    
                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)


    def ip(self, if_tag=None, version=None, active=True):
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
                if active:
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
                        if version == 'IPv6' and re.search(r"eth|srp", if_tag.name, re.I):
                            if_prefix.append(subnet_tag.name)
                            ra_line = self.lineNum
                
            self.skipTo(EndOfCommand)

        elif cmd == 'general-prefix':
            name = self.expect(String)
            ipaddress = self.expect(Literal)
            self.expect(Punctuation)
            address = ipaddress + "/" + self.expect(Literal)
            ipv6_general_prefixes[name] = IPy.IP(address)
            self.expect(EndOfCommand)
            
        elif cmd == 'helper-address':
            if self.accept(Keyword):
                self.expect(Literal)
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
            
        elif cmd == 'nd':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'prefix':
                nd_prefix = None
                default_prefix = self.accept(Keyword)
                if not default_prefix:
                    nd_prefix = self.expect(Literal) + self.expect(Punctuation) + self.expect(Literal)
                keyword = self.accept(Keyword)
                if keyword is None or not 'no-ad' in keyword:
                    if nd_prefix:
                        ra_prefix.append(nd_prefix)
            elif nextCmd == 'suppress-ra':
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

        else:
            self.skipTo(EndOfCommand)
            
        return (ra_suppress, ra_line, if_prefix, ra_prefix)

    def ssh(self):
        protocol = 'ssh'
        
        nextCmd = self.expect(Keyword)
        if nextCmd == 'server':
            if self.sshEnabled == False:
                t = taglib.tag("service", taglib.protocol_name(protocol))
                t.implied_by(taglib.env_tags.device, self.lineNum)
                self.sshEnabled = True
                t = taglib.tag("service", "SSHv2")
                t.implied_by(taglib.env_tags.device, self.lineNum)
            
                version = self.accept(Keyword)
                if not version == 'v2':
                    t = taglib.tag("service", "SSHv1")
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

def main():
    filename = taglib.default_filename
    content = open(filename).read()

    lexer = pygments.lexers.get_lexer_by_name("iosxr")
    formatter = TagsFormatter(fn=filename)

    pygments.highlight(content, lexer, formatter, sys.stdout)
    
    taglib.output_tagging_log()


if __name__ == '__main__':
    main()
