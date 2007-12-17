#!/usr/bin/perl -nl

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

# $Id$

/^Image\s*:\s*ExtremeXOS\s+version\s+(.*?)\s/ && do {
    print "$ARGV:$.: OS version--ExtremeXOS $1 {{context snapshot device--$ENV{SESSION_DEVICE}}}";
    print "$ARGV:$.: OS--ExtremeXOS {{context OS version--ExtremeXOS $1}}";
    print "$ARGV:$.: OS vendor--Extreme Networks {{context OS--ExtremeXOS}}";
};
