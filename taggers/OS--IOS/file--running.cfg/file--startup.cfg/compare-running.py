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
from os.path import dirname
from canner import taglib

def main():
    startup = file(taglib.default_filename)
    running = file(dirname(taglib.default_filename) + "running.cfg")

    m = re.compile(r'^version')
    line = startup.readline()
    lineno = 1
    while not m.match(line):
        line = startup.readline()
        lineno += 1

    line2 = running.readline()
    while not m.match(line2):
        line2 = running.readline()

    m = re.compile(r'clock-period')
    while line and line2 and line == line2:
        line = startup.readline()
        lineno += 1
        line2 = running.readline()
        if line and line2 and m.search(line):
            line = startup.readline()
            lineno += 1
            line2 = running.readline()


    if line != line2:
        t = taglib.tag("flag", "unsaved changes")
        t.implied_by(taglib.env_tags.snapshot, lineno)

    taglib.output_tagging_log()

if __name__ == '__main__':
    main()
