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

class POSIXPersonality(Personality):

    os_name = "POSIX"
    commands_to_probe = ("uname", )

    failed_command_patterns = (
        r"not found",
        )

    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.4, r"\w+BSD|Linux")
            self.examine_with_pattern(output, 0.2, r"Last login:.* from ")
        if command == "uname":
            self.examine_with_pattern(output, 0.9, r"\w+BSD|Linux")

    def setup(self, session):
        self.os_name = session.perform_command("uname").strip()
        session.prompt = r"(?m)^\r?\$ \Z"
        session.perform_command("exec env PS1='$ ' ENV= /bin/sh")
