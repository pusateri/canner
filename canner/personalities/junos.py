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

from . import Personality

class JUNOSPersonality(Personality):

    os_name = "JUNOS"

    commands_to_probe = ()


    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.8, r"--- JUNOS ")

    def setup(self, session):
        session.perform_command("set cli screen-length 0")
        session.perform_command("set cli screen-width 0")
