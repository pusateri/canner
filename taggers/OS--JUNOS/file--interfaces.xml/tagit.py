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

# $Id: tagit.py 3 2007-12-17 21:12:31Z keith $

from __future__ import with_statement

from canner import taglib
from lxml import etree
import os, sys

snapshotDevice = os.environ.get("SESSION_DEVICE", "unknown")
snapshotDeviceTag = "snapshot device--%s" % snapshotDevice

filename = sys.argv[1]
with file(filename) as f:
    tree = etree.parse(f)
top = tree.getroot()[0]
nsmap = top.nsmap
if None in nsmap:
    nsmap["x"] = nsmap[None]
    del nsmap[None]

def get_text(parentElem, xpath):
    elems = parentElem.xpath(xpath, nsmap)
    if elems:
        return elems[0].text

def out_attr(parentElem, xpath, kind, context):
    elems = parentElem.xpath(xpath, nsmap)
    for elem in elems:
        taglib.output_tag(filename, elem.sourceline,
                          kind + "--" + elem.text,
                          context=context)

physicalElems = top.xpath("x:physical-interface", nsmap)
for physicalElem in physicalElems:
    nameElems = physicalElem.xpath("x:name", nsmap)
    if not nameElems: continue
    nameElem = nameElems[0]
    physicalTag = "physical interface--%s %s" % (snapshotDevice, nameElem.text)
    taglib.output_tag(filename, nameElem.sourceline,
                      snapshotDeviceTag, context=physicalTag)

    out_attr(physicalElem, "x:speed", "speed", physicalTag)
    out_attr(physicalElem, "x:mtu", "MTU", physicalTag)
    out_attr(physicalElem, "x:if-type", "interface type", physicalTag)
    out_attr(physicalElem, "x:link-level-type", "link-level type", physicalTag)

    adminStatus = None
    adminStatusElems = physicalElem.xpath("x:admin-status", nsmap)
    if adminStatusElems:
        elem = adminStatusElems[0]
        adminStatus = elem.text
        taglib.output_tag(filename, elem.sourceline,
                          "admin status--" + adminStatus,
                          context=physicalTag)
    operStatus = None
    operStatusElems = physicalElem.xpath("x:oper-status", nsmap)
    if operStatusElems:
        operStatusElem = operStatusElems[0]
        operStatus = operStatusElem.text
        taglib.output_tag(filename, operStatusElem.sourceline,
                          "operational status--" + operStatus,
                          context=physicalTag)
    if adminStatus and operStatus and adminStatus != operStatus:
        taglib.output_tag(filename, operStatusElem.sourceline,
                          "flag--operational and admin status differ",
                          context=physicalTag)
