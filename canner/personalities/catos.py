#
# Copyright 2007-2009 !j Incorporated
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

class CatOSPersonality(Personality):

    os_name = "CatOS"
    in_command_interactions = (
        (r"--More--", " "),
        )
    commands_to_probe = ("show version", )


    def examine_evidence(self, command, output):
        if command == "__login__":
            self.examine_with_pattern(output, 0.2, r"User Access Verification")
        if command == "show version":
            self.examine_with_pattern(output, 0.8, r"Version NmpSW")

    def setup(self, session):
        if r"\(enable\)" not in session.prompt:
            self.enter_exec_mode()
        session.perform_command("set length 0")

    def enter_exec_mode(self, session):
        session.prompt = re.sub(r"\\Z$", r"\(enable\)\s?\Z", session.prompt)
        self.logger.debug("prompt changed to %r", session.prompt)

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

