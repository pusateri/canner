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

@ARGV = ($ENV{TRIGGER_FILENAME});
while (<>) {
    /^.*IOS.*Software.*\((.*?)\).*Version\s+([^,]+)/ && print <<EOF;
[
    {
        "location": "$ARGV:$.",
        "tag": "IOS type--$1",
        "implied_by": "device--$ENV{SESSION_DEVICE}"
    },
    {
        "location": "$ARGV:$.",
        "tag": "OS version--IOS $2",
        "implied_by": "IOS type--$1",
        "implies": "OS--IOS"
    },
EOF
    /^System image file.*"\w+:\/?(.*)"/ && print <<EOF;
    {
        "location": "$ARGV:$.",
        "tag": "system image file--$1",
        "implied_by": "device--$ENV{SESSION_DEVICE}"
    }
]
EOF
}
