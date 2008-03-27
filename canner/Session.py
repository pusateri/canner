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

import ConfigParser
import difflib
import logging
import os
import pexpect
import re
import sys
from . import error
from string import Template


class Session(object):

    def __init__(self, 
                 device, 
                 host=None, 
                 user=None,
                 password=None, 
                 exec_password=None,
                 command=None, 
                 bastion_host=None, 
                 bastion_command=None,
                 use_rc_files=True, 
                 rc_files=None,
                 should_log=False):

        self.logger = logging.getLogger("Session")

        defaults = {
            "command": "ssh $user@$host",
            "bastion_command": "ssh -t $bastion_host",
        }
        config = ConfigParser.SafeConfigParser(defaults)
        if use_rc_files:
            if not rc_files:
                rc_files = [os.path.expanduser("~/.cannerrc"), "cannerrc"]
            config.read(rc_files)
        def get(option, given, default=None):
            if given is not None:
                return given
            try:
                return config.get(device, option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass
            try:
                return config.get("DEFAULT", option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                return default

        self.device = device
        self.host = get("host", host, device)
        self.user = get("user", user)
        self.password = get("password", password)
        self.exec_password = get("exec_password", exec_password)

        command = get("command", command)
        bastion_host = get("bastion_host", bastion_host)
        bastion_command = get("bastion_command", bastion_command)
        if bastion_command:
            template = Template(bastion_command)
            mapping = dict()
            if bastion_host:
                mapping["bastion_host"] = bastion_host
            try:
                bastion_command = template.substitute(mapping)
            except KeyError:
                # the bastion command isn't complete, ignore it
                self.connect_command = command
                self.using_bastion = False
            else:
                self.connect_command = bastion_command + " " + command
                self.using_bastion = True
        else:
            self.connect_command = command
            self.using_bastion = False

        if not self.connect_command:
            raise error("Command not specified")

        self.personality = None
        self.child = None
        self.timeout = 90

        self.logfile = open("pexpect.log", "w") if should_log else None

    def start(self, login_only=False):
        self.logger.info("connecting to '%s'" % self.device)
        command = Template(self.connect_command).substitute(
            user=self.user,
            host=self.host,
            )
        self.logger.debug("spawning '%s'", command)
        self.child = pexpect.spawn(command, 
                                   logfile=self.logfile, 
                                   timeout=self.timeout)
        self.child.delaybeforesend = 0.5

        self.login()

        if not login_only:
            self.determine_prompt()
            self.determine_personality()
            self.personality.setup_session()
            self.os_name = self.personality.os_name

    def login(self):
        self.logger.info("logging in")

        self.login_info = ""
        sent_password = False
        timeout = 300

        while True:
            patterns = [
                pexpect.TIMEOUT,
                r"(?i)are you sure you want to continue connecting",
                r"(?im)^\r?(user name|username|login): ?",
                r"(?i)(Enter password.*?:|password: ?)",
                r"\r?Press any key to continue",
                r"(?i)(host|node)name nor servname provided, or not known",
                r"(?i)permission denied",
                r"(?i)connection closed by remote host",
                r"(?i)connection refused",
                r"(?i)Operation timed out",
                r"(?im)^\r?.{1,40}?[%#>] ?\Z",
                ]
            index = self.child.expect(patterns, timeout=timeout)
            self.login_info += self.child.before
            if self.child.after != pexpect.TIMEOUT:
                self.login_info += self.child.after
            timeout = self.timeout

            if index == 0: # timed out, hopefully we're at a prompt
                return

            elif index == 1: # new ssh certificate, always except
                self.child.sendline("yes")

            elif index == 2: # username,
                if sent_password:
                    raise error("Password incorrect")
                if not self.user:
                    raise error("User not specified")
                self.child.sendline(self.user)

            elif index == 3: # password
                if sent_password:
                    raise error("Password incorrect")
                if not self.password:
                    raise error("Password not specified")
                self.child.sendline(self.password)
                sent_password = True

            elif index == 4: # space required to continue
                self.child.send(" ")

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
                return

    def determine_prompt(self, text=None):
        self.logger.info("determining prompt")

        text = text or self.login_info
        last = text[text.rindex("\n")+1:]

        prompt = r"(?m)^\r?" + re.escape(last)
        prompt = re.sub(r"\d+", r"\d+", prompt)
        prompt = re.sub(r"\\([%>])((?:\\\s)?)$", r"[\1#]\2", prompt)
        prompt = prompt + r"\Z"

        self.prompt = prompt
        self.logger.debug("prompt pattern: %r", self.prompt)

    def determine_personality(self):
        self.logger.info("determining personality")

        from . import personalities
        
        self.child.sendline("show version")
        self.version_info = ""
        while True:
            index = self.child.expect([self.prompt, "--More--", r"\x08", 
                                       pexpect.TIMEOUT])
            self.version_info += self.child.before
            if index == 0: break
            if index == 1:
                self.child.send(" ")
            if index == 3:
                raise error("Problem determining personality")
        self.version_info = "".join(self.version_info.splitlines(True)[1:-1])
        self.version_info = re.sub(r"\r", "", self.version_info)

        factories = personalities.match(self.login_info + self.version_info)
        if not factories:
            raise error("No matching personalities")
        elif len(factories) > 1:
            self.logger.debug("multiple personalities: %r" % factories)
            raise error("More than one personality matched")
        self.personality = factories[0](self)

    def issue_command(self, cmd):
        self.logger.info("issuing command '%s'" % cmd)
        self.child.sendline(cmd)

        output = ""
        patterns = [self.prompt]
        patterns.extend(p[0] for p in self.personality.in_command_interactions)
        while True:
            index = self.child.expect(patterns)
            output += self.child.before
            if index == 0:
                break
            else:
                resp = self.personality.in_command_interactions[index - 1][1]
                if resp:
                    self.child.send(resp)

        scrub_echo_pattern = r"(?s)\r?\n?" + re.escape(cmd) + r"\s*?\n"
        output, numberFound = re.subn(scrub_echo_pattern, "", output, 1)
        if numberFound != 1:
            raise error("Problem issuing command")

        output = self.personality.cleanup_output(output)
        for pattern in self.personality.failed_command_patterns:
            if re.search(pattern, output):
                self.logger.debug("command failed\n" + output)
                return None

        self.logger.debug("output\n" + output)
        return output

    def interact(self):
        import struct, fcntl, termios, signal

        def setwinsize(sig=None, data=None):
            s = struct.pack("HHHH", 0, 0, 0, 0)
            a = struct.unpack("hhhh", fcntl.ioctl(sys.stdout.fileno(),
                                                  termios.TIOCGWINSZ, s))
            self.child.setwinsize(a[0], a[1])
        signal.signal(signal.SIGWINCH, setwinsize)
        setwinsize()

        self.child.sendline("")
        self.child.interact()

    def close(self):
        self.logger.info("disconnecting")
        if self.personality:
            self.personality.logout()
        if self.child:
            self.child.close()
