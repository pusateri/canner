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
from ..Session import SessionError
import pexpect
import re

class IOSPersonality(Personality):

    os_name = "IOS"
    in_command_interactions = (
        (r"--More--", " "),
        )

    @classmethod
    def match(cls, info):
        return re.search(r"Cisco (IOS|Internetwork Operating System) Software",
                         info)


    def setup_session(self):
        self.session.child.sendline("enable")
        index = self.session.child.expect([r"[Pp]assword: ?\Z",
                                           pexpect.TIMEOUT,
                                           self.session.prompt])
        if index == 0:
            if not self.session.execPassword:
                raise SessionError("Exec password not specified")
            self.session.child.sendline(self.session.execPassword)
            index = self.session.child.expect([r"[Pp]assword: ?\Z",
                                               pexpect.TIMEOUT,
                                               self.session.prompt])
            if index == 0:
                raise SessionError("Exec password not accepted")
            if index == 1:
                raise SessionError("Problem sending exec password")
        elif index == 1:
            raise SessionError("Problem entering exec mode")

        self.session.issueCmd("terminal length 0")
        self.session.issueCmd("terminal width 0")
