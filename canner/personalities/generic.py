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
import pexpect
import re
from . import Personality
from .. import error


class GenericPersonality(Personality):

    commands_to_probe = ()

    in_command_interactions = ()
    scrub_from_output_patterns = (
        r"\x1b\[[0-9;]*?[a-zA-Z]",
        r"\r",
        r"\x08+(\s+\x08+)?",
        )
    failed_command_patterns = ()

    logout_command = "exit"


    def __init__(self):
        self.logger = logging.getLogger("GenericPersonality")
        self.confidence = 25 if type(self) == GenericPersonality else 10


    def perform_command(self, session, command):
        if command == "__login__":
            return self.login(session)
        elif command == "__logout__":
            return self.logout(session)
        elif command == "__determine_prompt__":
            return self.determine_prompt(session)
        elif command == "__setup__":
            return self.setup(session)
        elif command.startswith("__"):
            self.logger.debug("Unknown special command: '%s'" % command)
            return None
        else:
            return self.perform_cli_command(session, command)


    #
    # Callbacks
    #


    def update_confidence(self, command, output):
        pass


    #
    # Internal methods
    #


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
                r"\r?Press any key to continue",
                r"(?i)(host|node)name nor servname provided, or not known",
                r"(?i)permission denied",
                r"(?i)connection closed by remote host",
                r"(?i)connection refused",
                r"(?i)Operation timed out",
                r"(?im)^\r?.{1,40}?[%#>] ?\Z",
                ]
            index = session.connection.expect(patterns, timeout=timeout)
            capturebuf += session.connection.before
            if session.connection.after != pexpect.TIMEOUT:
                capturebuf += session.connection.after
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

            elif index == 4: # space required to continue
                session.connection.send(" ")

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

            elif index == 10: # hopefully a prompt
                break

        return capturebuf


    def logout(self, session):
        session.connection.sendline(self.logout_command)
        session.connection.expect(pexpect.EOF)


    def determine_prompt(self, session):
        text = session.perform_command("__login__")
        last = text[text.rindex("\n")+1:]

        prompt = r"(?m)^\r?" + re.escape(last)
        prompt = re.sub(r"\d+", r"\d+", prompt)
        prompt = re.sub(r"\\([%>])((?:\\\s)?)$", r"[\1#]\2", prompt)
        prompt = prompt + r"\Z"

        return prompt


    def setup(self, session):
        pass


    def perform_cli_command(self, session, command):
        session.connection.sendline(command)

        output = ""
        patterns = [session.prompt]
        patterns.extend(p[0] for p in self.in_command_interactions)
        while True:
            index = session.connection.expect(patterns)
            output += session.connection.before
            if index == 0:
                break
            else:
                resp = self.in_command_interactions[index - 1][1]
                if resp:
                    session.connection.send(resp)

        scrub_echo_pattern = r"(?s)\r?\n?" + re.escape(command) + r"\s*?\n"
        output, number_found = re.subn(scrub_echo_pattern, "", output, 1)
        if number_found != 1:
            raise error("Problem issuing command")

        output = self.cleanup_output(output)
        for pattern in self.failed_command_patterns:
            if re.search(pattern, output):
                self.logger.debug("command failed\n" + output)
                return None

        self.logger.debug("output\n" + output)
        return output


    def cleanup_output(self, output):
        for pattern in self.scrub_from_output_patterns:
            output = re.sub(pattern, "", output)
        return output

