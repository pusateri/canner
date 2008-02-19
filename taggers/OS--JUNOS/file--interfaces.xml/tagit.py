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

from canner import taglib
from lxml import etree
import os, sys

filename = taglib.default_filename
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

def tag_attrs(parentElem, xpath, kind, context):
    elems = parentElem.xpath(xpath, nsmap)
    for elem in elems:
        t = taglib.tag(kind, elem.text)
        t.implied_by(context, elem.sourceline)


physicalElems = top.xpath("x:physical-interface", nsmap)
for physicalElem in physicalElems:
    nameElems = physicalElem.xpath("x:name", nsmap)
    if not nameElems: continue
    nameElem = nameElems[0]
    physical_tag = taglib.tag("physical interface",
                              "%s %s" % (taglib.env_tags.device.name,
                                         nameElem.text))
    physical_tag.implies(taglib.env_tags.device, nameElem.sourceline)                                        

    tag_attrs(physicalElem, "x:speed", "speed", physical_tag)
    tag_attrs(physicalElem, "x:mtu", "MTU", physical_tag)
    tag_attrs(physicalElem, "x:if-type", "interface type", physical_tag)
    tag_attrs(physicalElem, "x:link-level-type", "link-level type", physical_tag)

    adminStatus = None
    adminStatusElems = physicalElem.xpath("x:admin-status", nsmap)
    if adminStatusElems:
        elem = adminStatusElems[0]
        adminStatus = elem.text
        t = taglib.tag("admin status", adminStatus)
        t.implied_by(physical_tag, elem.sourceline)

    operStatus = None
    operStatusElems = physicalElem.xpath("x:oper-status", nsmap)
    if operStatusElems:
        operStatusElem = operStatusElems[0]
        operStatus = operStatusElem.text
        t = taglib.tag("operational status", operStatus)
        t.implied_by(physical_tag, operStatusElem.sourceline)

    if adminStatus and operStatus and adminStatus != operStatus:
        t = taglib.tag("flag", "operational and admin status differ")
        t.implied_by(physical_tag, operStatusElem.sourceline)

taglib.output_tagging_log()
