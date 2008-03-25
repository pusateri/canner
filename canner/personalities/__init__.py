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

import logging
import re
import pexpect
import pkg_resources

class Personality(object):

    in_command_interactions = ()
    scrub_from_output_patterns = (
        r"\x1b\[[0-9;]*?[a-zA-Z]",
        r"\r",
        r"\x08+(\s+\x08+)?",
        )
    failed_command_patterns = ()

    logout_command = "exit"

    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger("Personality")

    def setup_session(self):
        pass

    def logout(self):
        self.session.child.sendline(self.logout_command)
        self.session.child.expect(pexpect.EOF)

    def cleanup_output(self, output):
        for pattern in self.scrub_from_output_patterns:
            output = re.sub(pattern, "", output)
        return output


def match(info):
    personalities = [ep.load() for ep in
                     pkg_resources.iter_entry_points("canner.personalities")]
    return [p for p in personalities if p.match(info)]
