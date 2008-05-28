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

# verify /md5 (flash:c2801-advsecurityk9-mz.124-10a.bin) = 3f61cf7ee066f423f0411689080dc22b

data = open(taglib.default_filename).read()
m = re.search(r"verify.*\(.*[:/]([^:/]+)\) = (\w+)", data)
if m:
    filename, hash = m.groups()
    t = taglib.tag("system image hash","%s %s" % (filename, hash))
    t.implied_by(taglib.env_tags.snapshot)

taglib.output_tagging_log()
