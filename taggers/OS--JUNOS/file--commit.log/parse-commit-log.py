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

import sys, os, re
from canner import taglib

lines = open(taglib.default_filename).readlines(1024)
commitPattern = re.compile(r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d ...) by (.*?) via (.*)\n')

m = commitPattern.match(lines[0])
if m:
    dateString, user, source = m.groups()
    t = taglib.tag("config user", user)
    t.implied_by(taglib.env_tags.snapshot, 1)

    if len(lines) > 1:
        m = commitPattern.match(lines[1])
        if not m:
            comment = lines[1].rstrip('\n')
            t = taglib.tag("config log", comment)
            t.implied_by(taglib.env_tags.snapshot, 2)

taglib.output_tagging_log()
