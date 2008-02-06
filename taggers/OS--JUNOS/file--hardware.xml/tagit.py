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

def tag_attr(parentElem, xpath, kind, context):
    elems = parentElem.xpath(xpath, nsmap)
    if elems:
        t = taglib.tag(kind, elems[0].text)
        t.implied_by(context, elems[0].sourceline)
        return t

chassisList = top.xpath("x:chassis", nsmap)
for chassisElem in chassisList:
    nameElem = chassisElem.xpath("x:name", nsmap)[0]
    chassis_tag = taglib.tag("chassis","%s %s" % (taglib.env_tags.device.name, 
                                                  nameElem.text))
    chassis_tag.implies(taglib.env_tags.device, nameElem.sourceline)

    tag_attr(chassisElem,
             "x:serial-number",
             "chassis serial number",
             chassis_tag)
    tag_attr(chassisElem,
             "x:description",
             "chassis description",
             chassis_tag)

    moduleList = chassisElem.xpath("x:chassis-module", nsmap)
    for moduleElem in moduleList:
        modNameElem = moduleElem.xpath("x:name", nsmap)[0]
        module_tag = taglib.tag("module", "%s %s %s" % (
            taglib.env_tags.device.name, nameElem.text, modNameElem.text))
        module_tag.implied_by(taglib.env_tags.snapshot, modNameElem.sourceline)
        module_tag.implies(chassis_tag, modNameElem.sourceline)

        tag_attr(moduleElem,
                 "x:description",
                 "module description",
                 module_tag)
        t = tag_attr(moduleElem,
                     "x:serial-number",
                     "module serial number",
                     module_tag)
        tag_attr(moduleElem,
                 "x:part-number",
                 "module part number",
                 t)
        tag_attr(moduleElem,
                 "x:version",
                 "module version",
                 module_tag)

taglib.output_tagging_log()
