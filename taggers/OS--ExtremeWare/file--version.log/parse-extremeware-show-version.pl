#!/usr/bin/perl -w

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

# $Id: parse-extremeware-show-version.pl 2 2007-12-17 21:12:04Z keith $

@ARGV = ($ENV{TRIGGER_FILENAME});
while (<>) {
    /^Image\s*:\s*ExtremeWare\s+Version\s+(.*?)\s/i && print <<EOF;
[
    {
        "location": "$ARGV:$.",
        "tag": "OS version--ExtremeWare $1",
        "implied_by": "snapshot device--$ENV{SESSION_DEVICE}",
        "implies": "OS--ExtremeWare"
    }
]
EOF
}
