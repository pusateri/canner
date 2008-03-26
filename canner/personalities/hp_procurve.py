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
import pexpect
import re

class HPProCurvePersonality(Personality):
    # TODO: figure out how to handle files longer than 1000 lines

    os_name = "HPProCurve"
    logout_command = "logout"

    @classmethod
    def match(cls, info):
        return re.search(r"HP.* ProCurve ", info)


    def setup_session(self):
        self.session.issueCmd("terminal length 1000")
        self.session.issueCmd("terminal width 1920")

    def logout(self):
        self.session.child.sendline(self.logout_command)
        while True:
            index = self.session.child.expect(
                    [pexpect.EOF,
                     r"Do you want to log out \[y/n\]\? ",
                     r"(?i)save current configuration \[y/n\]\?"])
            if index == 0: break
            elif index == 1:
                self.session.child.sendline("y")
            elif index == 2:
                self.session.child.sendline("n")
