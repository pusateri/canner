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
import genshi.template.text
import urllib
from . import error
from .session import Session


class Task(object):
    def __init__(self, engine, trigger_spec):
        self.engine = engine
        self.trigger_spec = trigger_spec
        self.trigger_re = re.compile(trigger_spec)

    def handle(self, tag):
        if self.trigger_re.match(tag):
            self.run(tag)

    def run(self, trigger):
        pass


class DirectoryTask(Task):
    def __init__(self, engine, trigger_spec, dir):
        super(DirectoryTask, self).__init__(engine, trigger_spec)
        self.dir = dir
        self.already_run = False

    def run(self, trigger):
        if self.already_run:
            return
        self.already_run = True

        self.engine.logger.debug("loading tag dir '%s'" %  
                self.engine.strip_tag_dir(self.dir))

        for name in os.listdir(self.dir):
            path = os.path.join(self.dir, name)
            task = None

            if name.startswith('.') or name.endswith('~'):
                pass
            elif os.path.isdir(path):
                spec = re.sub(r"\\_\\_ANY\\_\\_", r".*?",
                        re.escape(name) + ("$" if "--" in name else "--"))
                task = DirectoryTask(self.engine, spec, path)
            elif name.endswith(".cli"):
                task = CLITask(self.engine, self.trigger_spec, path)
            else:
                task = TaggerTask(self.engine, self.trigger_spec, path)

            if task:
                self.engine.add_task(task)

    def __repr__(self):
        return "<DirectoryTask trigger='%s' dir='%s'>" % (
                self.trigger_spec, self.dir)


class TaggerTask(Task):
    def __init__(self, engine, trigger_spec, tagger):
        super(TaggerTask, self).__init__(engine, trigger_spec)
        self.tagger = tagger

    def run(self, trigger):
        tagger_short_name = self.engine.strip_tag_dir(self.tagger)

        self.engine.logger.info("running tagger '%s'" % tagger_short_name)

        kind, _, name = trigger.partition("--")

        env = dict(os.environ)
        env["TRIGGER_KIND"], env["TRIGGER_NAME"] = kind, name
        if kind == "file":
            env["TRIGGER_FILENAME"] = name
        for k, v in self.engine.session_info.iteritems():
            env["SESSION_%s" % re.sub(r'([A-Z])', r'_\1', k).upper()] = str(v)

        p = subprocess.Popen([self.tagger], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data, errors = p.communicate()

        tagger_name = "--".join(tagger_short_name.split("/"))
        log_filename = self.engine.log_file_path(tagger_name)

        tagging_log = None
        tagging_error = None
        
        with open(log_filename, "w") as f:
            print >>f, "===", self.tagger
            print >>f
            print >>f, "=== Environment"
            print >>f
            for k in sorted(env):
                print >>f, "%s=%s" % (k, env[k])
            print >>f
            print >>f
            print >>f, "=== Tag Data (stdout)"
            print >>f
            f.write(data)
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
                    tagging_log = simplejson.loads(data)
                except ValueError, e:
                    tagging_error = (
                            "error parsing output of tagger '%s':\n%s" %
                            (tagger_short_name, e))
                    print >>f
                    print >>f
                    print >>f, "=== Error parsing tag data"
                    print >>f
                    print >>f, str(e)
            else:
                tagging_error = ("error running tagger '%s':\n%s" %
                                (tagger_short_name, errors))
                print >>f, "=== Process failed: return code %d" % p.returncode
                                
        if tagging_error:
            self.engine.logger.error(tagging_error)
            self.engine.add_file(log_filename)
            self.engine.add_tagref("error--tagger failed", path=log_filename, 
                    context="snapshot--" + self.engine.session_info["id"])
            return
            
        for entry in tagging_log:
            tag = entry["tag"]
            if tag.startswith("file--"):
                self.engine.add_file_tagref(tag[6:])
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
                self.engine.add_tagref(tag, tagger_name, filename, line_num, 
                        properties)

                if "implies" in entry:
                    self.engine.add_tagref(entry["implies"], tagger_name, 
                            filename, line_num, context=tag)


class CLITask(Task):
    def __init__(self, engine, trigger_spec, source_path):
        super(CLITask, self).__init__(engine, trigger_spec)
        self.source_path = source_path

    def run(self, trigger):
        if not self.engine.session:
            return

        trigger_kind, _, trigger_name = trigger.partition("--")

        m = re.search(r"/file--([^/]+)\.cli$", self.source_path)
        assert m, "malformed cli command filename"
        name = m.group(1)
        name = name.replace("__TRIGGER_NAME__", urllib.quote_plus(trigger_name))

        with open(self.source_path) as f:
            source = f.read().rstrip("\n")
        template = genshi.template.text.TextTemplate(source)
        vars = dict(re=re,
                trigger=trigger, 
                trigger_kind=trigger_kind, 
                trigger_name=trigger_name)
        command = template.generate(**vars).render()

        content = self.engine.session.perform_command(command)

        if content:
            self.engine.add_file_tagref(name, content)




class Engine(object):

    def __init__(self, taggers_dir, session=None, timestamp=None):
        self.taggers_dir = taggers_dir
        self.session = session
        self.timestamp = timestamp
        self.tasks = list()
        self.tagrefs = defaultdict(list)
        self.logger = logging.getLogger("Engine")
        self.log_file_number = 0


    def run(self):
        self.make_package_structure()

        startup_task = DirectoryTask(self, r"file--sessionInfo$", 
                self.taggers_dir)
        self.add_task(startup_task)

        si = self.session_info = dict()

        if self.session:
            si["id"] = base64.encodestring(uuid.uuid4().bytes)[:-3]
            si["timestamp"] = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            si["device"] = self.session.device
            si["user"] = self.session.user
            si["osName"] = self.session.os_name
            s = "\n".join("%s=%s" % (k, si[k]) for k in sorted(si))
            self.add_file_tagref("sessionInfo", s)
            self.add_file_tagref("login.log", self.session.login_info)

        else:
            if not os.path.exists("sessionInfo"):
                raise error("sessionInfo file not found")
            with open("sessionInfo") as f:
                for line in f:
                    k, _, v = line.partition("=")
                    si[k.strip()] = v.strip()
            for name in self.interesting_files():
                self.add_file_tagref(name)

        self.syntax_highlight_files()
        self.write_info_file()


    def add_task(self, task):
        self.logger.debug("adding %s triggered by r'%s'" % 
                (type(task).__name__, task.trigger_spec))
        self.tasks.append(task)
        for tag in self.tagrefs.keys():
            task.handle(tag)


    def add_tagref(self, tag, tagger="canner", filename=None, line=None,
            properties={}, **kw):
        filename = filename or ""
        line = int(line or 0)
        tagref = dict(tagger=tagger, filename=filename, line=line)
        tagref.update(properties)
        tagref.update(kw)

        self.tagrefs[tag].append(tagref)
        self.logger.debug("added tag '%s' from %s:%d" %
                          (tag, tagref["filename"], tagref["line"]))

        if len(self.tagrefs[tag]) == 1:
            # This is the first time we've seen the tag.  Notify all 
            # existing tasks.
            self.logger.debug("notifying tasks about '%s'" % tag)
            for task in list(self.tasks):
                task.handle(tag)


    def add_file_tagref(self, filename, content=None):
        self.add_file(filename, content)
        ctx = "snapshot--" + self.session_info["id"]
        self.add_tagref("file--" + filename, "canner", filename, context=ctx)


    def add_file(self, filename, content=None):
        if content is not None:
            assert not os.path.exists(filename)
            with open(filename, "w") as f:
                f.write(content)


    def strip_tag_dir(self, path):
        common = os.path.commonprefix([self.taggers_dir + "/", path])
        return path[len(common):]


    def log_file_path(self, name):
        path = os.path.join("Contents", "Logs", 
                "%03d--%s.log" % (self.log_file_number, name))
        self.log_file_number += 1
        return path


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
            if file_tag not in self.tagrefs:
                self.logger.warning("creating missing file tag for '%s'",
                                    filename)
                self.add_file_tagref(filename)

            ancestors = set()
            tocheck = set()
            tocheck.add(file_tag)
            while tocheck:
                for tagref in self.tagrefs[tocheck.pop()]:
                    if "context" not in tagref: continue
                    context_tag = tagref["context"]
                    if context_tag not in ancestors \
                            and not context_tag.startswith("snapshot--"):
                        ancestors.add(context_tag)
                        tocheck.add(context_tag)

            syntaxes = [t.partition("--")[0] for t in ancestors]
            self.logger.debug("for file '%s' found syntaxes %r",
                    filename, syntaxes)

            self.syntax_highlight_file(filename, *syntaxes)



    def get_tag_names_by_kind(self, kind):
        matches = set(t for t in self.tagrefs if t.startswith(kind + "--"))
        return [tag.partition("--")[2] for tag in matches]


    def get_tag_name_by_kind(self, kind):
        names = self.get_tag_names_by_kind(kind)
        return names[0] if names else None


    def write_info_file(self):
        unreferenced_tags = [k for k, v in self.tagrefs.iteritems() if not v]
        for tag in unreferenced_tags:
            del self.tagrefs[tag]

        user = self.get_tag_name_by_kind("config user")
        log = self.get_tag_name_by_kind("config log")

        info = dict()
        info["tags"] = self.tagrefs
        info["device"] = self.session_info["device"]
        info["snapshotID"] = self.session_info["id"]
        info["timestamp"] = self.session_info["timestamp"]
        if user: info["user"] = user
        if log: info["log"] = log

        with open(os.path.join("Contents", "info.json"), "w") as f:
            simplejson.dump(info, f, sort_keys=True, indent=2)

