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

snapshotID = os.environ.get("SESSION_ID", "unknown")
snapshotIDTag = "snapshot ID--%s" % snapshotID
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
    if elems:
        tag = kind + "--" + elems[0].text
        taglib.output_tag(filename, elems[0].sourceline, tag, context=context)
        return tag

chassisList = top.xpath("x:chassis", nsmap)
for chassisElem in chassisList:
    nameElem = chassisElem.xpath("x:name", nsmap)[0]
    chassisTag = "chassis--%s %s" % (snapshotDevice, nameElem.text)
    taglib.output_tag(filename, nameElem.sourceline,
                      snapshotDeviceTag, context=chassisTag)

    out_attr(chassisElem,
             "x:serial-number",
             "chassis serial number",
             chassisTag)
    out_attr(chassisElem,
             "x:description",
             "chassis description",
             chassisTag)

    moduleList = chassisElem.xpath("x:chassis-module", nsmap)
    for moduleElem in moduleList:
        modNameElem = moduleElem.xpath("x:name", nsmap)[0]
        moduleTag = "module--%s %s %s" % (
            snapshotDevice, nameElem.text, modNameElem.text)
        taglib.output_tag(filename, modNameElem.sourceline,
                          moduleTag, context=snapshotIDTag)
        taglib.output_tag(filename, modNameElem.sourceline,
                          chassisTag, context=moduleTag)

        out_attr(moduleElem,
                 "x:description",
                 "module description",
                 moduleTag)
        t = out_attr(moduleElem,
                     "x:serial-number",
                     "module serial number",
                     moduleTag)
        out_attr(moduleElem,
                 "x:part-number",
                 "module part number",
                 t)
        out_attr(moduleElem,
                 "x:version",
                 "module version",
                 moduleTag)
