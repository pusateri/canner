#
# Copyright 2009 !j Incorporated
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

from . import Personality
import re

class NetScalerPersonality(Personality):

    os_name = "NetScaler"
    commands_to_probe = ("show version", )

    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.4,
                    "\n Done\r")
            self.examine_with_pattern(output, 0.4, r"\n> \Z")

        elif command == "show version":
            self.examine_with_pattern(output, 0.8, r"NetScaler")
