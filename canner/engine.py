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

from __future__ import with_statement

from collections import defaultdict
import sys
import os
import logging
import datetime
import pygments
import pygments.formatters
import pygments.lexers
import re
import subprocess
import socket
import uuid
import base64
import simplejson
from . import error
from . import plistlib
from .session import Session


class Engine(object):

    def __init__(self, taggers_dir, session=None, timestamp=None):
        self.taggers_dir = taggers_dir
        self.session = session
        self.timestamp = timestamp

        self.logger = logging.getLogger("Engine")

        self.tag_refs = defaultdict(list)
        self.pending_tag_dirs = defaultdict(list)
        self.pending_commands = list()
        self.taggers = defaultdict(list)
        self.log_file_number = 0


    def run(self):
        self.make_package_structure()
        self.generate_tags()
        self.write_info_plist()



    def add_tag_dir(self, tag, dirname):
        command_file = os.path.join(dirname, "Command")
        if os.path.isfile(command_file):
            self.add_command(tag, command_file)
        if self.tag_refs[tag]:
            self.load_tag_dir(tag, dirname)
        else:
            self.pending_tag_dirs[tag].append((tag, dirname))
            self.logger.debug("waiting to load tag dir '%s'" %
                              self._strip_tag_dir(dirname))

    def add_command(self, tag, source_filename):
        kind, _, name = tag.partition("--")
        assert kind == "file"
        with open(source_filename) as f:
            command = f.read().rstrip("\n")
        self.logger.debug("waiting to issue command '%s' for tag '%s'" %
                          (command, tag))
        self.pending_commands.append((command, name))

    def add_tagger(self, tag, tagger):
        self.taggers[tag].append(tagger)
        ran_tagger = False
        if "--" in tag:
            if tag in self.tag_refs:
                self.run_tagger(tagger, tag)
                ran_tagger = True
        else:
            for t in [t for t in self.tag_refs if t.startswith(tag + "--")]:
                self.run_tagger(tagger, t)
                ran_tagger = True
        if not ran_tagger:
            self.logger.debug("waiting to run tagger '%s'" %
                              self._strip_tag_dir(tagger))


    def add_tag_ref(self, tag, tagger="canner", filename=None, line=None,
                  properties={}, **kw):
        filename = filename or ""
        line = int(line or 0)
        tag_ref = dict(tagger=tagger, filename=filename, line=line)
        tag_ref.update(properties)
        tag_ref.update(kw)
        self.tag_refs[tag].append(tag_ref)
        self.logger.debug("added tag '%s' from %s:%d" %
                          (tag, tag_ref["filename"], tag_ref["line"]))

        if len(self.tag_refs[tag]) == 1:
            # This is the first time we've seen the tag.  Run any waiting
            # taggers and load any pending directories.
            wildcard_tag = tag[0:tag.index("--")]
            for t in tag, wildcard_tag:
                for tagger in self.taggers[t]:
                    self.run_tagger(tagger, tag)
                for pending_tag, path in self.pending_tag_dirs[t]:
                    self.load_tag_dir(pending_tag, path)
                    del self.pending_tag_dirs[t]

    def add_file(self, filename, content=None):
        if content is not None:
            with open(filename, "w") as f:
                f.write(content)

    def add_file_tag_ref(self, filename, content=None):
        self.add_file(filename, content)
        ctx = "snapshot--" + self.session_info["id"]
        self.add_tag_ref("file--" + filename, "canner", filename, context=ctx)

    def _strip_tag_dir(self, path):
        common = os.path.commonprefix([self.taggers_dir + "/", path])
        return path[len(common):]



    def load_tag_dir(self, tag, dir):
        self.logger.debug("loading tag dir '%s'" %  self._strip_tag_dir(dir))
        for name in os.listdir(dir):
            if name.startswith('.') or name.endswith('~') or name == 'Command':
                continue
            path = os.path.join(dir, name)

            if os.path.isdir(path):
                self.add_tag_dir(name, path)
            else:
                self.add_tagger(tag, path)

    def run_tagger(self, tagger, tag):
        self.logger.info("running tagger '%s'" % self._strip_tag_dir(tagger))

        kind, _, name = tag.partition("--")

        env = dict(os.environ)
        env["TRIGGER_KIND"], env["TRIGGER_NAME"] = kind, name
        if kind == "file":
            env["TRIGGER_FILENAME"] = name
        for k, v in self.session_info.iteritems():
            env["SESSION_%s" % re.sub(r'([A-Z])', r'_\1', k).upper()] = str(v)

        p = subprocess.Popen([tagger], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tag_data, errors = p.communicate()

        tagger_name = "--".join(self._strip_tag_dir(tagger).split("/"))
        log_filename = \
            os.path.join("Contents", "Logs",
                         "%03d--%s.log" % (self.log_file_number, tagger_name))
        self.log_file_number += 1

        tagging_log = None
        tagging_error = None
        
        with open(log_filename, "w") as f:
            print >>f, "===", tagger
            print >>f
            print >>f, "=== Environment"
            print >>f
            for k in sorted(env):
                print >>f, "%s=%s" % (k, env[k])
            print >>f
            print >>f
            print >>f, "=== Tag Data (stdout)"
            print >>f
            f.write(tag_data)
            if errors:
                print >>f
                print >>f
                print >>f, "=== Error Output"
                print >>f
                f.write(errors)
            print >>f
            print >>f

            if p.returncode == 0:
                print >>f, "=== Process exited normally"
                try:
                    tagging_log = simplejson.loads(tag_data)
                except ValueError, e:
                    tagging_error = (
                            "error parsing output of tagger '%s':\n%s" %
                            (self._strip_tag_dir(tagger), e))
                    print >>f
                    print >>f
                    print >>f, "=== Error parsing tag data"
                    print >>f
                    print >>f, str(e)
            else:
                tagging_error = ("error running tagger '%s':\n%s" %
                                (self._strip_tag_dir(tagger), errors))
                print >>f, "=== Process failed: return code %d" % p.returncode
                                
        if tagging_error:
            self.logger.error(tagging_error)
            self.add_file(log_filename)
            self.add_tag_ref("error--tagger failed", path=log_filename, 
                           context="snapshot--" + self.session_info["id"])
            return
            
        for entry in tagging_log:
            tag = entry["tag"]
            if tag.startswith("file--"):
                self.add_file_tag_ref(tag[6:])
            else:
                try:
                    filename, _, line_num = entry["location"].partition(":")
                except KeyError:
                    filename = line_num = None

                properties = dict()
                if "sort_name" in entry:
                    properties["sortName"] = entry["sort_name"]
                if "display_name" in entry:
                    properties["displayName"] = entry["display_name"]
                if "implied_by" in entry:
                    properties["context"] = entry["implied_by"]
                self.add_tag_ref(tag, tagger_name, filename, line_num, 
                        properties)

                if "implies" in entry:
                    self.add_tag_ref(entry["implies"], tagger_name, filename,
                                   line_num, context=tag)

    def make_package_structure(self):
        dirs = (
            "Contents",
            "Contents/Logs",
            "Contents/Resources",
            )
        for dir in dirs:
            if not os.path.exists(dir): os.mkdir(dir)
        with open("Contents/PkgInfo", "w") as f:
            f.write("????????")


    def actively_generate_tags(self):
        si = self.session_info = dict(
            id = base64.encodestring(uuid.uuid4().bytes)[:-3],
            timestamp = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            device = self.session.device,
            user = self.session.user,
            osName = self.session.os_name,
            )
        s = "\n".join("%s=%s" % (k, si[k]) for k in sorted(si))
        self.add_file_tag_ref("sessionInfo", s)

        self.add_file_tag_ref("login.log", self.session.login_info)

        while self.pending_commands:
            command, filename = self.pending_commands.pop()
            assert not os.path.exists(filename)
            content = self.session.perform_command(command)
            if content:
                self.add_file_tag_ref(filename, content)

    def passively_generate_tags(self):
        if not os.path.exists("sessionInfo"):
            raise error("sessionInfo file not found")

        si = self.session_info = {}
        with open("sessionInfo") as f:
            for line in f:
                k, _, v = line.partition("=")
                si[k.strip()] = v.strip()
        for name in self.interesting_files():
            self.add_file_tag_ref(name)

    def interesting_files(self):
        for name in os.listdir("."):
            if name.startswith(".") or name.endswith("~") \
                    or name in ("Contents", "pexpect.log"):
                continue
            yield name

    def syntax_highlight_file(self, filename, *syntaxes):
        with open(filename) as f:
                content = f.read()
                
        lexers = set()
        for syntax in syntaxes:
            try:
                lexers.add(pygments.lexers.get_lexer_by_name(syntax, 
                    stripnl=False))
            except pygments.util.ClassNotFound:
                pass
        if not lexers:
            try:
                lexers.add(pygments.lexers.guess_lexer_for_filename(
                            filename, content, stripnl=False))
            except pygments.util.ClassNotFound:
                pass
        if len(lexers) == 1:
            lexer = lexers.pop()
        else:
            if len(lexers) > 1:
                self.logger.error("multiple lexers found for '%s'" % filename)
            lexer = pygments.lexers.get_lexer_by_name("text", stripnl=False)

        formatter = pygments.formatters.get_formatter_by_name(
                "canner", full=True, encoding="utf-8",
                linenos="inline", cssfile="code-default.css")

        self.logger.info("syntax highlighting file '%s' as '%s'" % (
            filename, lexer.name))

        out_filename = os.path.join("Contents", "Resources", filename + ".html")
        out_dir = os.path.dirname(out_filename)
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(out_filename, "w") as f:
            result = pygments.highlight(content, lexer, formatter, f)

    def syntax_highlight_files(self):
        for filename in self.interesting_files():
            file_tag = "file--" + filename
            if file_tag not in self.tag_refs:
                self.logger.warning("creating missing file tag for '%s'",
                                    filename)
                self.add_file_tag_ref(filename)

            ancestors = set()
            tocheck = set()
            tocheck.add(file_tag)
            while tocheck:
                for tag_ref in self.tag_refs[tocheck.pop()]:
                    if "context" not in tag_ref: continue
                    context_tag = tag_ref["context"]
                    if context_tag not in ancestors \
                            and not context_tag.startswith("snapshot--"):
                        ancestors.add(context_tag)
                        tocheck.add(context_tag)

            syntaxes = [t.partition("--")[0] for t in ancestors]
            self.logger.debug("for file '%s' found syntaxes %r",
                    filename, syntaxes)

            self.syntax_highlight_file(filename, *syntaxes)


    def generate_tags(self):
        self.load_tag_dir('internal--startup', self.taggers_dir)

        if self.session:
            self.actively_generate_tags()
        else:
            self.passively_generate_tags()

        self.syntax_highlight_files()


    def get_tag_names_by_kind(self, kind):
        matches = set(t for t in self.tag_refs if t.startswith(kind + "--"))
        return [tag.partition("--")[2] for tag in matches]

    def get_tag_name_by_kind(self, kind):
        names = self.get_tag_names_by_kind(kind)
        return names[0] if names else None

    def write_info_plist(self):
        unreferenced_tags = [k for k, v in self.tag_refs.iteritems() if not v]
        for tag in unreferenced_tags:
            del self.tag_refs[tag]

        ts = datetime.datetime.strptime(self.session_info["timestamp"],
                                       "%Y-%m-%dT%H:%M:%S")
        user = self.get_tag_name_by_kind("config user")
        log = self.get_tag_name_by_kind("config log")

        info = dict()
        info["tags"] = self.tag_refs
        info["device"] = self.session_info["device"]
        info["snapshotID"] = self.session_info["id"]
        info["timestamp"] = ts
        if user: info["user"] = user
        if log: info["log"] = log

        plist = os.path.join("Contents", "Info.plist")
        plistlib.writePlist(info, plist)
        
        info["timestamp"] = self.session_info["timestamp"]
        with open(os.path.join("Contents", "info.json"), "w") as f:
            simplejson.dump(info, f, sort_keys=True, indent=2)
