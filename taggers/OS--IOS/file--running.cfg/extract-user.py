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

# $Id: extract-user.py 2 2007-12-17 21:12:04Z keith $

import sys, os, re
from canner import taglib

snapshotID = os.environ.get("SESSION_ID", "unknown")
snapshotIDTag = "snapshot ID--%s" % snapshotID

data = open(sys.argv[1]).read(1024).strip('\n')
m = re.search(r'NVRAM config last updated at .*? by (.*)$', data, re.MULTILINE)
if m:
    num = data[0:m.start(0)].count('\n')
    taglib.output_tag(sys.argv[1], num, 'config user--%s' % m.group(1),
                      context=snapshotIDTag)
