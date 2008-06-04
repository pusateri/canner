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

class FreeBSDPersonality(Personality):

    os_name = "FreeBSD"
    commands_to_probe = ("uname", )

    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.6, r"FreeBSD")
            self.examine_with_pattern(output, 0.6, r"Last login:.* from ")
        if command == "uname":
            self.examine_with_pattern(output, 0.9, r"FreeBSD")
