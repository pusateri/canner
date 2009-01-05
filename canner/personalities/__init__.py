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
import operator
import pexpect
import pkg_resources
import re
from .. import error

ANSI_CODE_RE = r"\x1b\[[0-9;]*?[a-zA-Z]"

class Personality(object):
    
    in_command_interactions = ()
    scrub_from_output_patterns = (
        ANSI_CODE_RE,
        r"\r",
        r"\x08+(\s+\x08+)?",
        )
    failed_command_patterns = ()

    logout_command = "exit"

    commands_to_probe = ()


    def __init__(self):
        self.logger = logging.getLogger("personality")
        self.confidence_measures = list()
        self.confidence = 0

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

    def login(self, session):
        raise error("This personality does not know how to login")

    def logout(self, session):
        session.connection.sendline(self.logout_command)
        session.connection.expect(pexpect.EOF)

    def determine_prompt(self, session):
        text = session.perform_command("__login__")
        try:
            last = text[text.rindex("\n")+1:]
        except ValueError:
            last = text

        prompt = re.escape(last)
        prompt = re.sub(r"\d+", r"\d+", prompt)
        prompt = re.sub(r"\\([%>])((?:\\\s)?)$", r"[\1#]\2", prompt)
        prompt = r"(?m)^\r?(" + ANSI_CODE_RE + r")*" + prompt + r"\Z"

        return prompt

    def setup(self, session):
        pass

    def perform_cli_command(self, session, command):
        session.connection.sendline(command)

        output = []
        patterns = [session.prompt]
        patterns.extend(p[0] for p in self.in_command_interactions)
        while True:
            session.abort_if_timeout_exceeded()
            prev_len = len(session.connection.buffer)
            try:
                index = session.connection.expect(patterns)
            except pexpect.TIMEOUT:
                read = len(session.connection.buffer) - prev_len
                self.logger.debug("Got timeout, read %d", read)
                # Ignore timeouts as long as some data was read.
                if not read:
                    raise
                # Only keep the last 1K of the buffer to help perfomance
                # when receiving large files.  This could potentially break
                # really long patterns.
                output.append(session.connection.buffer[:-1024])
                session.connection.buffer = session.connection.buffer[-1024:]
            else:
                output.append(session.connection.before)
                if index == 0:
                    break
                else:
                    resp = self.in_command_interactions[index - 1][1]
                    if resp:
                        session.connection.send(resp)
        output = ''.join(output)

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


    def add_confidence(self, measure):
        self.confidence_measures.append(measure)
        self.confidence = 1.0 - reduce(operator.mul, 
                (1.0 - c for c in self.confidence_measures), 1.0)

    def examine_with_pattern(self, text, confidence, pattern):
        if re.search(pattern, text):
            self.add_confidence(confidence)

