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

from __future__ import with_statement

import sys
import IPy; IPy.check_addr_prefixlen = False
from lxml import etree

def const(text):
    def _const(element):
        return text, None
    return _const

def tag(element):
    return element.tag, None

def text(element):
    return element.text, None

def ip_address(text):
    ip = IPy.IP(text)
    sortName = ("%08x" if ip.version() == 4 else "%032x") % ip.int()
    return ip.strCompressed(wantprefixlen=0), dict(sortName=sortName)

def ip_subnet(text):
    ip = IPy.IP(text, make_net=True)
    ip.NoPrefixForSingleIp = False
    sortName = ("%08x" if ip.version() == 4 else "%032x") % ip.int()
    return ip.strCompressed(), dict(sortName=sortName)

def protocol_name(name):
    protocolLabelDict = {'bgp':'BGP', 'dhcp':'DHCP', 'finger':'FINGER', 'ftp':'FTP',
                         'http':'HTTP', 'https':'HTTPS', 'igmp':'IGMP', 'MLD':'MLD', 'mpls':'MPLS',
                         'msdp':'MSDP', 'netconf':'NETCONF', 'ospf':'OSPF', 'pim':'PIM', 'rip':'RIP',
                         'ripng':'RIPng', 'scp':'SCP', 'service-deployment':'SDXD', 'ssh':'SSH',
                         'telnet':'TELNET', 'telnets':'TELNETS', 'xnm-clear-text':'XNM',
                         'xnm-ssl':'XNMS'}
    return protocolLabelDict.get(name, name)

def output_tag(filename, line, qname, properties=None, **kw):
    properties = properties or {}
    properties.update(kw)
    propString = " ".join("{{%s %s}}" % (k, v) for k, v in properties.items())
    print "%s:%d: %s %s" % (filename, line, qname, propString)

def output_tags(patterns, top, filename, **kw):
    nsmap = top.nsmap
    if None in nsmap:
        nsmap['x'] = nsmap[None]
        del nsmap[None]

    for pattern, kind, func in patterns:
        for e in top.xpath(pattern, nsmap):
            name, properties = func(e)
            tag = "%s--%s" % (kind, name)
            output_tag(filename, e.sourceline, tag, properties, **kw)

def main(patterns, *args):
    import os
    snapshotDevice = os.environ.get("SESSION_DEVICE", "unknown")
    snapshotDeviceTag = "snapshot device--%s" % snapshotDevice

    filename = sys.argv[1]
    with file(filename) as f:
        tree = etree.parse(f)
    top = tree.getroot()[0]
    output_tags(patterns, top, filename, context=snapshotDeviceTag)
    for func in args:
        func(top, filename)
