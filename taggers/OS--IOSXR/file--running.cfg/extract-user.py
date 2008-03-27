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

data = open(taglib.default_filename).read(1024).strip('\n')
m = re.search(r'Last configuration change at .*? by (.*)$', data, re.MULTILINE)
if m:
    num = data[0:m.start(0)].count('\n')
    t = taglib.tag("config user", m.group(1))
    t.implied_by(taglib.env_tags.snapshot, num)
    
taglib.output_tagging_log()
