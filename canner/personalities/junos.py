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

from .generic import GenericPersonality

class JUNOSPersonality(GenericPersonality):

    os_name = "JUNOS"

    commands_to_probe = ("show version", )

    def setup(self, session):
        session.perform_command("set cli screen-length 0")
        session.perform_command("set cli screen-width 0")

    def update_confidence(self, command, output):
        if command == "__login__":
            if "--- JUNOS " in output:
                self.confidence = 100
            else:
                self.confidence = 0

