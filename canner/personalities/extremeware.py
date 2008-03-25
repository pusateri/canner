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

from . import Personality, register
import pexpect

class ExtremeWarePersonality(Personality):

    os_name = "ExtremeWare"
    in_command_interactions = (
        (r"Press <SPACE> to continue or <Q> to quit:", " "),
        )
    logout_command = "quit"

    def logout(self):
        self.session.child.sendline(self.logout_command)
        while True:
            index = self.session.child.expect(
                    [pexpect.EOF,
                     r"configuration changes\? \(y/n\)"])
            if index == 0: break
            elif index == 1:
                self.session.child.sendline("n")

register(r"(?i)Image.*ExtremeWare", ExtremeWarePersonality)
