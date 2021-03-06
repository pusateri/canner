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

import logging
import pexpect
import re
from . import Personality
from .. import error


class BootstrapPersonality(Personality):

    commands_to_probe = ()

    in_command_interactions = (
        (r"--More--", " "),
        )

    def __init__(self):
        super(BootstrapPersonality, self).__init__()
        self.confidence = 0.50


    def examine_evidence(self, command, output):
        pass


    def login(self, session):
        capturebuf = ""
        sent_password = False
        timeout = 300

        while True:
            patterns = [
                pexpect.TIMEOUT,
                r"(?i)are you sure you want to continue connecting",
                r"(?im)^\r?(user name|username|user|login): ?",
                r"(?i)(Enter password.*?:|password: ?)",
                r"\r?(Press any key to continue|Press RETURN to get started)",
                r"(?i)(host|node)name nor servname provided, or not known",
                r"(?i)permission denied",
                r"(?i)connection closed by remote host",
                r"(?i)connection refused",
                r"(?i)Operation timed out",
                r"(?i)Host key verification failed",
                r"(?i)[\r\n]+.{1,40}?[%#>$] ?(?:\(enable\) ?)?\Z",
                ]
            index = session.connection.expect(patterns, timeout=timeout)
            capturebuf += session.connection.before
            if session.connection.after != pexpect.TIMEOUT:
                capturebuf += session.connection.after
            else:
                # Clear out the buffer so we don't see the data
                # (hopefully the prompt) later.
                session.connection.buffer = ""
            timeout = session.timeout

            if index == 0: # timed out, hopefully we're at a prompt
                break

            elif index == 1: # new ssh certificate, always except
                session.connection.sendline("yes")

            elif index == 2: # username,
                if sent_password:
                    raise error("Password incorrect")
                if not session.user:
                    raise error("User not specified")
                session.connection.sendline(session.user)

            elif index == 3: # password
                if sent_password:
                    raise error("Password incorrect")
                if not session.password:
                    raise error("Password not specified")
                session.connection.sendline(session.password)
                sent_password = True

            elif index == 4: # key required to continue
                session.connection.send("\r")

            elif index == 5:
                raise error("Unknown host")
            elif index == 6:
                raise error("Permission denied")
            elif index == 7:
                raise error("Connection closed by remote host")
            elif index == 8:
                raise error("Connection refused")
            elif index == 9:
                raise error("Connection timed out")
            elif index == 10:
                raise error("SSH host key verification failed")

            elif index == 11: # hopefully a prompt
                break

        return capturebuf


    def setup(self, session):
        raise error("A suitable personality was not found.")

