#
# Copyright 2007-2008 !j Incorporated
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

import canner
from . import Personality
import pexpect
import re

class IOSXRPersonality(Personality):

    os_name = "IOSXR"
    in_command_interactions = (
        (r"--More--", " "),
        )

    @classmethod
    def match(cls, info):
        return re.search(r"Cisco IOS XR Software",
                         info)


    def setup_session(self):
        self.session.child.sendline("enable")
        index = self.session.child.expect([r"[Pp]assword: ?\Z",
                                           pexpect.TIMEOUT,
                                           self.session.prompt])
        if index == 0:
            if not self.session.exec_password:
                raise canner.error("Exec password not specified")
            self.session.child.sendline(self.session.exec_password)
            index = self.session.child.expect([r"[Pp]assword: ?\Z",
                                               pexpect.TIMEOUT,
                                               self.session.prompt])
            if index == 0:
                raise canner.error("Exec password not accepted")
            if index == 1:
                raise canner.error("Problem sending exec password")
        elif index == 1:
            raise canner.error("Problem entering exec mode")

        self.session.issue_command("terminal length 0")
        self.session.issue_command("terminal width 0")
