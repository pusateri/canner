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

import sys, os, re, urllib
from canner import taglib

lines = open(taglib.default_filename).readlines(1024)
m = re.match(r"MD5 \((.*?)\) = ([0-9a-zA-Z]+)", lines[0])
if m:
    path, hash = m.groups()

    t = taglib.tag("file signature", "%s %s" % (path, hash))
    t.implies(taglib.env_tags.trigger, 1)
    t.implies(taglib.tag("file MD5 hash", hash), 1)

taglib.output_tagging_log()
