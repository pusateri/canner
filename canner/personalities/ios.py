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
import canner
import pexpect
import re

class IOSPersonality(Personality):

    os_name = "IOS"
    in_command_interactions = (
        (r"--More--", " "),
        )
    commands_to_probe = ("show version", )


    def examine_evidence(self, command, output):
        if command == "show version":
            self.examine_with_pattern(output, 0.8,
                    r"Cisco (IOS|Internetwork Operating System) Software")

    def setup(self, session):
        session.connection.sendline("enable")
        index = session.connection.expect([r"[Pp]assword: ?\Z",
                                           pexpect.TIMEOUT,
                                           session.prompt])
        if index == 0:
            if not session.exec_password:
                raise canner.error("Exec password not specified")
            session.connection.sendline(session.exec_password)
            index = session.connection.expect([r"[Pp]assword: ?\Z",
                                               pexpect.TIMEOUT,
                                               session.prompt])
            if index == 0:
                raise canner.error("Exec password not accepted")
            if index == 1:
                raise canner.error("Problem sending exec password")
        elif index == 1:
            raise canner.error("Problem entering exec mode")

        session.perform_command("terminal length 0")
        session.perform_command("terminal width 0")

