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

# $Id$

import pygments
import pygments.formatters
from pygments.formatter import Formatter
import pygments.lexers
from pygments.token import *
from canner.taglib import *
import sys
import traceback
import IPy; IPy.check_addr_prefixlen = False
import os
import re

EndOfCommand = Token.EndOfCommand

snapshotID = os.environ.get("SESSION_ID", "unknown")
snapshotIDTag = "snapshot ID--%s" % snapshotID
snapshotDevice = os.environ.get("SESSION_DEVICE", "unknown")
snapshotDeviceTag = "snapshot device--%s" % snapshotDevice

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


    def outputTag(self, tag, lineNum=None, **props):
        if lineNum is None:
            lineNum = self.lineNum
        propStr = " ".join("{{%s %s}}" % (k, v) for k, v in props.items() if v)
        self.outFile.write(self.tagFormat % (lineNum, tag, propStr))


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
            self.outFile.write('#error: %s:%d: %s (\'%s\' line %d)\n' % (
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

                elif cmd == 'hostname':
                    self.outputTag("hostname--" + self.accept(String),
                                   context=snapshotDeviceTag)
                    self.expect(EndOfCommand)

                elif cmd == 'interface':
                    self.interface()

                elif cmd == 'ip':
                    self.ip()

                elif cmd == 'radius-server':
                    self.radius()

                elif cmd == 'router':
                    self.skipTo(EndOfCommand)

                elif cmd == 'username':
                    self.outputTag("user--" + self.accept(String),
                                   context=snapshotDeviceTag)
                    self.skipTo(EndOfCommand)

                # elif cmd == 'version':
                #     self.outputTag("version--" + self.accept(String))
                #     self.expect(EndOfCommand)

                else:
                    self.skipTo(EndOfCommand)

            except UnexpectedToken:
                self.skipTo(EndOfCommand)


    def interface(self):
        name = self.expect(Name)
        ifTag = "interface--%s %s" % (snapshotDevice, name)
        self.outputTag(ifTag, context=snapshotIDTag)
        self.outputTag(snapshotDeviceTag, context=ifTag)
        self.outputTag("interface type--" + re.sub(r"[0-9/]+$", "", name),
                       context=ifTag)
        self.expect(EndOfCommand)

        while True:
            if self.accept(Whitespace) is None:
                return
            op = self.accept(Operator)
            cmd = self.expect(Keyword)

            if False:
                pass

            elif cmd == 'ip':
                self.ip(ifTag)

            else:
                self.skipTo(EndOfCommand)

    def radius(self):
        cmd = self.expect(Keyword)

        if cmd == 'host':
            self.outputTag("RADIUS server--" + self.expect(Literal),
                           context=snapshotDeviceTag)
            self.skipTo(EndOfCommand)

    def ip(self, ifTag=None):
        cmd = self.expect(Keyword)

        if False:
            pass

        elif cmd == 'address':
            address = self.expect(Literal)
            netmask = self.expect(Literal)

            ip = IPy.IP('%s/%s' % (address, netmask))
            sortName = ("%08x" if ip.version() == 4 else "%032x") % ip.int()
            addressTag = "IPv4 interface address--%s" % ip.strCompressed(wantprefixlen=0)
            self.outputTag(addressTag,
                           sortName=sortName,
                           context=ifTag)

            ip = IPy.IP('%s/%s' % (address, netmask), make_net = True)
            ip.NoPrefixForSingleIp = False
            subnetTag = "IPv4 subnet--%s" % ip.strCompressed()
            sortName = ("%08x" if ip.version() == 4 else "%032x") % ip.int()
            self.outputTag(subnetTag,
                           sortName=sortName,
                           context=addressTag)

            self.skipTo(EndOfCommand)

        elif cmd == 'domain name' or cmd == 'domain-name':
            self.outputTag("domain name--" + self.expect(String),
                           context=snapshotDeviceTag)
            self.expect(EndOfCommand)

        elif cmd == 'http':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'server':
                self.outputTag("service--HTTP", context=snapshotDeviceTag)
            elif nextCmd == 'secure-server':
                self.outputTag("service--HTTPS", context=snapshotDeviceTag)

            self.skipTo(EndOfCommand)

        elif cmd == 'name-server':
            self.outputTag("name server--" + self.expect(Literal),
                           context=snapshotDeviceTag)
            self.expect(EndOfCommand)

        elif cmd == 'scp':
            nextCmd = self.expect(Keyword)
            if nextCmd == 'server':
                nextCmd = self.expect(Keyword)
                if nextCmd == 'enable':
                    self.outputTag("service--%s" % protocol_name(cmd), context=snapshotDeviceTag)

            self.skipTo(EndOfCommand)

        elif cmd == 'ssh':
            if self.sshEnabled == False:
                self.outputTag("service--%s" % protocol_name(cmd), context=snapshotDeviceTag)
                self.sshEnabled = True
            nextCmd = self.expect(Keyword)
            if nextCmd == 'version':
                version = self.expect(Literal)
                if version == '2':
                    self.outputTag("service--SSHv2", context=snapshotDeviceTag)
                    self.outputTag("service--%s" % protocol_name(cmd), context=snapshotDeviceTag)
                elif version == '1':
                    self.outputTag("service--SSHv1", context=snapshotDeviceTag)
                    self.outputTag("service--%s" % protocol_name(cmd), context=snapshotDeviceTag)
            self.skipTo(EndOfCommand)

        else:
            self.skipTo(EndOfCommand)

    def router(self):
        pass

def main():
    filename = sys.argv[1]
    content = open(filename).read()

    lexer = pygments.lexers.guess_lexer_for_filename(filename, content)
    formatter = TagsFormatter(fn=filename)

    pygments.highlight(content, lexer, formatter, sys.stdout)


if __name__ == '__main__':
    main()
