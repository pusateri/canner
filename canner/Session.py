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
import pkg_resources
import operator
import itertools
from . import error
from string import Template
from collections import defaultdict


class Session(object):

    def __init__(self, **kw): 
        self.logger = logging.getLogger("Session")

        self.configure(**kw)

        self.connection = None
        self.timeout = 90
        self.command_cache = dict()

        self.candidate_personalities = list()
        for ep in pkg_resources.iter_entry_points("canner.personalities"):
            cls = ep.load()
            self.candidate_personalities.append(cls())
        self.update_candidates()


    def start(self, login_only=False):
        self.connect()
        self.login_info = self.perform_command("__login__")
        self.update_candidates("__login__", self.login_info)

        if login_only:
            return

        self.prompt = self.perform_command("__determine_prompt__")
        self.update_candidates("___determine_prompt__", self.prompt)

        cands = self.candidate_personalities

        # The 25% manditory split is just pulled from thin air.
        while cands[0].confidence < 0.75 \
                or (cands[0].confidence - cands[1].confidence) < 0.25:
            probe_commands = [cmd 
                    for pers in cands
                    for cmd in pers.commands_to_probe
                    if cmd not in self.command_cache]
            if not probe_commands:
                break
            output = self.perform_command(probe_commands[0])
            self.update_candidates(probe_commands[0], output)

        self.logger.debug("personality %s won", 
                self.personality.__class__.__name__)

        self.perform_command("__setup__")

        self.os_name = self.personality.os_name

    def perform_command(self, command, use_cache=True):
        if use_cache and command in self.command_cache:
            self.logger.info("using cached command '%s'" % command)
            return self.command_cache[command]

        self.logger.info("performing command '%s'" % command)
        self.logger.debug("delegating to '%s'", 
                self.personality.__class__.__name__)
        output = self.personality.perform_command(self, command)
        self.command_cache[command] = output
        return output


    def interact(self):
        import struct, fcntl, termios, signal

        def setwinsize(sig=None, data=None):
            s = struct.pack("HHHH", 0, 0, 0, 0)
            a = struct.unpack("hhhh", fcntl.ioctl(sys.stdout.fileno(),
                                                  termios.TIOCGWINSZ, s))
            self.connection.setwinsize(a[0], a[1])
        signal.signal(signal.SIGWINCH, setwinsize)
        setwinsize()

        self.connection.sendline("")
        self.connection.interact()


    def close(self):
        self.logger.info("disconnecting")
        self.perform_command("__logout__")
        if self.connection:
            self.connection.close()



    #
    # Internal methods
    #


    def configure(self,
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

        self.logfile = open("pexpect.log", "w") if should_log else None

    def connect(self):
        self.logger.info("connecting to '%s'" % self.device)
        command = Template(self.connect_command).substitute(
            user=self.user,
            host=self.host,
            )
        self.logger.debug("spawning '%s'", command)
        self.connection = pexpect.spawn(command, 
                                   logfile=self.logfile, 
                                   timeout=self.timeout)
        self.connection.delaybeforesend = 0.5


    def update_candidates(self, command=None, output=None):
        if command:
            for personality in self.candidate_personalities:
                personality.examine_evidence(command, output)

        self.candidate_personalities.sort(
                key=operator.attrgetter("confidence"), reverse=True)
        self.personality = self.candidate_personalities[0]

        for candidate in self.candidate_personalities:
            if candidate.confidence:
                self.logger.debug("candidate: %3d%% %s" % (
                    100 * candidate.confidence, candidate.__class__.__name__))


