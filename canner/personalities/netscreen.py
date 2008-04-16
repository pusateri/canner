#
# Copyright 2008 !j Incorporated
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

class NetscreenPersonality(Personality):
    
    os_name = "ScreenOS"
    commands_to_probe = ("get system", "get config", )
            
    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.4, 
                    "\nRemote Management Console\r")
            self.examine_with_pattern(output, 0.4, r"\nns-> \Z")

        elif command == "get system":
            self.examine_with_pattern(output, 0.8, r"Product Name: NetScreen")

        elif command == "show version":
            if output is None:
                self.add_confidence(0.4)

