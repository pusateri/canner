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

# $Id: Session.py 12 2008-01-25 19:52:56Z pusateri $

import ConfigParser
import difflib
import logging
import os
import pexpect
import re
import sys
from string import Template


class Personality(object):

    inCommandInteractions = ()
    scrubFromOutputPatterns = (
        r"\x1b\[[0-9;]*?[a-zA-Z]",
        r"\r",
        )
    failedCommandPatterns = ()

    logoutCommand = "exit"

    def __init__(self, session):
        self.session = session
        self.logger = logging.getLogger("Session.Personality")

    def setupSession(self):
        pass

    def logout(self):
        self.session.child.sendline(self.logoutCommand)
        self.session.child.expect(pexpect.EOF)

    def cleanupOutput(self, output):
        for pattern in self.scrubFromOutputPatterns:
            output = re.sub(pattern, "", output)
        return output


class IOSPersonality(Personality):

    DETECT_RE = r"Cisco (IOS|Internetwork Operating System) Software"

    osName = "IOS"
    inCommandInteractions = (
        (r"--More--", " "),
        )

    def __init__(self, session):
        super(IOSPersonality, self).__init__(session)
        self.isPrivilaged = False

    def setupSession(self):
        if not self.isPrivilaged:
            self.session.child.sendline("enable")
            index = self.session.child.expect(
                    [r"[Pp]assword: ?\Z",
                     pexpect.TIMEOUT,
                     self.session.prompt])
            if index == 0:
                if not self.session.execPassword:
                    raise SessionError("Exec password not specified")
                self.session.child.sendline(self.session.execPassword)
                self.session.child.expect(self.session.prompt)
            if index == 1:
                raise SessionError("Problem entering exec mode")
            self.isPrivilaged = True
        self.session.issueCmd("terminal length 0")
        self.session.issueCmd("terminal width 0")


class JUNOSPersonality(Personality):

    DETECT_RE = r"JUNOS "

    osName = "JUNOS"

    def setupSession(self):
        self.session.issueCmd("set cli screen-length 0")
        self.session.issueCmd("set cli screen-width 0")


class ExtremeWarePersonality(Personality):

    DETECT_RE = r"(?i)Image.*ExtremeWare"

    osName = "ExtremeWare"
    inCommandInteractions = (
        (r"Press <SPACE> to continue or <Q> to quit:", " "),
        )
    logoutCommand = "quit"

    def logout(self):
        self.session.child.sendline(self.logoutCommand)
        while True:
            index = self.session.child.expect(
                    [pexpect.EOF,
                     r"configuration changes\? \(y/n\)"])
            if index == 0: break
            elif index == 1:
                self.session.child.sendline("n")


class ExtremeXOSPersonality(Personality):
    DETECT_RE = r"Image.*ExtremeXOS"

    osName = "ExtremeXOS"
    failedCommandPatterns = (
        r"Invalid input detected",
        )
    logoutCommand = "quit"

    def setupSession(self):
        self.session.issueCmd("disable clipaging")

    def logout(self):
        self.session.child.sendline(self.logoutCommand)
        while True:
            index = self.session.child.expect(
                    [pexpect.EOF,
                     r"configuration changes to primary.cfg\? \(y/N\)"])
            if index == 0: break
            elif index == 1:
                self.session.child.sendline("n")


class HPProCurvePersonality(Personality):
    # TODO: figure out how to handle files longer than 1000 lines
    DETECT_RE = r"Image stamp"

    osName = "HPProCurve"
    logoutCommand = "logout"

    def setupSession(self):
        self.session.issueCmd("terminal length 1000")
        self.session.issueCmd("terminal width 1920")

    def logout(self):
        self.session.child.sendline(self.logoutCommand)
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


PERSONALITY_CLASSES = (IOSPersonality, JUNOSPersonality, ExtremeXOSPersonality,
                       ExtremeWarePersonality, HPProCurvePersonality)


class SessionError(StandardError):
    pass


class Session(object):

    def __init__(self, device, host=None, user=None,
                 password=None, execPassword=None,
                 command=None, bastionHost=None, bastionCommand=None,
                 useCannerRC=True, shouldLog=False):

        self.logger = logging.getLogger("Session")

        defaults = {
            "command": "ssh $user@$host",
            "bastion_command": "ssh -t $bastion_host",
        }
        config = ConfigParser.SafeConfigParser(defaults)
        if useCannerRC:
            config.read([os.path.expanduser("~/.cannerrc"), "cannerrc"])
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
        self.execPassword = get("exec_password", execPassword)

        command = get("command", command)
        bastionHost = get("bastion_host", bastionHost)
        bastionCommand = get("bastion_command", bastionCommand)
        if bastionCommand:
            template = Template(bastionCommand)
            mapping = dict()
            if bastionHost:
                mapping["bastion_host"] = bastionHost
            try:
                bastionCommand = template.substitute(mapping)
            except KeyError:
                # the bastion command isn't complete, ignore it
                self.connectCommand = command
                self.usingBastion = False
            else:
                self.connectCommand = bastionCommand + " " + command
                self.usingBastion = True
        else:
            self.connectCommand = command
            self.usingBastion = False

        if not self.connectCommand:
            raise SessionError("Command not specified")

        self.personality = None
        self.child = None
        self.timeout = -1

        self.logfile = open("pexpect.log", "w") if shouldLog else None

    def start(self):
        self.logger.info("connecting to '%s'" % self.device)
        command = Template(self.connectCommand).substitute(
            user=self.user,
            host=self.host,
            )
        self.logger.debug("spawning '%s'", command)
        self.child = pexpect.spawn(command, logfile=self.logfile)
        self.child.delaybeforesend = 0.5

        self.login()
        self.determinePrompt()
        self.determinePersonality()
        self.personality.setupSession()
        self.osName = self.personality.osName

    def login(self):
        self.logger.info("logging in")

        self.loginInfo = ""
        sentPassword = False
        timeout = 300

        while True:
            patterns = [
                pexpect.TIMEOUT,
                r"(?i)are you sure you want to continue connecting",
                r"(?im)^\r?(username|login): ?",
                r"(?i)password: ?",
                r"\r?Press any key to continue",
                r"(?i)(host|node)name nor servname provided, or not known",
                r"(?i)permission denied",
                r"(?i)connection closed by remote host",
                r"(?i)connection refused",
                r"(?i)Operation timed out",
                r"(?im)^\r?.{1,40}?[%#>] ?\Z",
                ]
            index = self.child.expect(patterns, timeout=timeout)
            self.loginInfo += self.child.before
            if self.child.after != pexpect.TIMEOUT:
                self.loginInfo += self.child.after
            timeout = self.timeout

            if index == 0: # timed out, hopefully we're at a prompt
                return

            elif index == 1: # new ssh certificate, always except
                self.child.sendline("yes")

            elif index == 2: # username,
                if sentPassword:
                    raise SessionError("Password incorrect")
                if not self.user:
                    raise SessionError("User not specified")
                self.child.sendline(self.user)

            elif index == 3: # password
                if sentPassword:
                    raise SessionError("Password incorrect")
                if not self.password:
                    raise SessionError("Password not specified")
                self.child.sendline(self.password)
                sentPassword = True

            elif index == 4: # space required to continue
                self.child.send(" ")

            elif index == 5:
                raise SessionError("Unknown host")
            elif index == 6:
                raise SessionError("Permission denied")
            elif index == 7:
                raise SessionError("Connection closed by remote host")
            elif index == 8:
                raise SessionError("Connection refused")
            elif index == 9:
                raise SessionError("Connection timed out")

            elif index == 10: # hopefully a prompt
                return

    def determinePrompt(self, text=None):
        self.logger.info("determining prompt")

        text = text or self.loginInfo
        last = text[text.rindex("\n")+1:]

        prompt = r"(?m)^\r?" + re.escape(last)
        prompt = re.sub(r"\d+", r"\d+", prompt)
        prompt = re.sub(r"\\([%>])((?:\\\s)?)$", r"[\1#]\2", prompt)
        prompt = prompt + r"\Z"

        self.prompt = prompt
        self.logger.debug("prompt pattern: %r", self.prompt)

    def determinePersonality(self):
        self.logger.info("determining personality")

        self.child.sendline("show version")
        self.versionInfo = ""
        while True:
            index = self.child.expect([self.prompt, "--More--", r"\x08", pexpect.TIMEOUT])
            self.versionInfo += self.child.before
            if index == 0: break
            if index == 1:
                self.child.send(" ")
            if index == 3:
                raise SessionError("Problem determining personality")
        self.versionInfo = "".join(self.versionInfo.splitlines(True)[1:-1])
        self.versionInfo = re.sub(r"\r", "", self.versionInfo)

        clslst = [p for p in PERSONALITY_CLASSES
                  if re.search(p.DETECT_RE, self.versionInfo)]
        if not clslst:
            raise SessionError("No matching personalities")
        elif len(clslst) > 1:
            self.logger.debug("multiple personalities: %r" % clslst)
            raise SessionError("More than one personality matched")
        self.personality = clslst[0](self)

    def issueCmd(self, cmd):
        self.logger.info("issuing command '%s'" % cmd)
        self.child.sendline(cmd)

        output = ""
        while True:
            patterns = [self.prompt]
            patterns.extend(p[0] for p in self.personality.inCommandInteractions)
            index = self.child.expect(patterns)
            output += self.child.before
            if index == 0: break
            if self.personality.inCommandInteractions[index-1][1]:
                self.child.send(self.personality.inCommandInteractions[index-1][1])

        scrubCommandEchoPattern = r"(?s)\r?\n?" + re.escape(cmd) + r"\s*?\n"
        output, numberFound = re.subn(scrubCommandEchoPattern, "", output, 1)
        if numberFound != 1:
            raise SessionError("Problem issuing command")

        output = self.personality.cleanupOutput(output)
        for pattern in self.personality.failedCommandPatterns:
            if re.search(pattern, output):
                self.logger.debug("command failed\n" + output)
                return None

        self.logger.debug("output\n" + output)
        return output


    def close(self):
        self.logger.info("disconnecting")
        if self.personality:
            self.personality.logout()
        if self.child:
            self.child.close()
