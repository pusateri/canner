#
# Copyright 2007-2008 !j Incorporated
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

from .ios import IOSPersonality
import re

class IOSXRPersonality(IOSPersonality):

    os_name = "IOS XR"

    def examine_evidence(self, command, output):
        if command == "show version":
            self.examine_with_pattern(output, 0.8, r"Cisco IOS XR Software")
