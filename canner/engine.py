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

    def __init__(self, taggersDir, session=None, timestamp=None):
        self.taggersDir = taggersDir
        self.session = session
        self.timestamp = timestamp

        self.logger = logging.getLogger("Engine")

        self.tagRefs = defaultdict(list)
        self.pendingTagDirs = defaultdict(list)
        self.pendingCommands = list()
        self.taggers = defaultdict(list)
        self.logFileNumber = 0;


    def run(self):
        self.makePackageStructure()
        self.generateTags()
        self.writeInfoPlist()



    def addTagDir(self, tag, dirname):
        commandFile = os.path.join(dirname, "Command")
        if os.path.isfile(commandFile):
            self.addCommand(tag, commandFile)
        if self.tagRefs[tag]:
            self.loadTagDir(tag, dirname)
        else:
            self.pendingTagDirs[tag].append((tag, dirname))
            self.logger.debug("waiting to load tag dir '%s'" %
                              self._stripTagDir(dirname))

    def addCommand(self, tag, sourceFilename):
        kind, _, name = tag.partition("--")
        assert kind == "file"
        with open(sourceFilename) as f:
            command = f.read().rstrip("\n")
        self.logger.debug("waiting to issue command '%s' for tag '%s'" %
                          (command, tag))
        self.pendingCommands.append((command, name))

    def addTagger(self, tag, tagger):
        self.taggers[tag].append(tagger)
        ranTagger = False
        if "--" in tag:
            if tag in self.tagRefs:
                self.runTagger(tagger, tag)
                ranTagger = True
        else:
            for t in [t for t in self.tagRefs if t.startswith(tag + "--")]:
                self.runTagger(tagger, t)
                ranTagger = True
        if not ranTagger:
            self.logger.debug("waiting to run tagger '%s'" %
                              self._stripTagDir(tagger))


    def addTagRef(self, tag, tagger="canner", filename=None, line=None,
                  properties={}, **kw):
        filename = filename or ""
        line = int(line or 0)
        tagRef = dict(tagger=tagger, filename=filename, line=line)
        tagRef.update(properties)
        tagRef.update(kw)
        self.tagRefs[tag].append(tagRef)
        self.logger.debug("added tag '%s' from %s:%d" %
                          (tag, tagRef["filename"], tagRef["line"]))

        if len(self.tagRefs[tag]) == 1:
            # This is the first time we've seen the tag.  Run any waiting
            # taggers and load any pending directories.
            wildcardTag = tag[0:tag.index("--")]
            for t in tag, wildcardTag:
                for tagger in self.taggers[t]:
                    self.runTagger(tagger, tag)
                for pendingTag, path in self.pendingTagDirs[t]:
                    self.loadTagDir(pendingTag, path)
                    del self.pendingTagDirs[t]

    def addFile(self, filename, content=None):
        if content is not None:
            with open(filename, "w") as f:
                f.write(content)

    def addFileTagRef(self, filename, content=None):
        self.addFile(filename, content)
        ctx = "snapshot--" + self.sessionInfo["id"]
        self.addTagRef("file--" + filename, "canner", filename, context=ctx)

    def _stripTagDir(self, path):
        common = os.path.commonprefix([self.taggersDir + "/", path])
        return path[len(common):]



    def loadTagDir(self, tag, dir):
        self.logger.debug("loading tag dir '%s'" %  self._stripTagDir(dir))
        for name in os.listdir(dir):
            if name.startswith('.') or name.endswith('~') or name == 'Command':
                continue
            path = os.path.join(dir, name)

            if os.path.isdir(path):
                self.addTagDir(name, path)
            else:
                self.addTagger(tag, path)

    def runTagger(self, tagger, tag):
        self.logger.info("running tagger '%s'" % self._stripTagDir(tagger))

        kind, _, name = tag.partition("--")

        env = dict(os.environ)
        env["TRIGGER_KIND"], env["TRIGGER_NAME"] = kind, name
        if kind == "file":
            env["TRIGGER_FILENAME"] = name
        for k, v in self.sessionInfo.iteritems():
            env["SESSION_%s" % re.sub(r'([A-Z])', r'_\1', k).upper()] = str(v)

        p = subprocess.Popen([tagger], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tagData, errors = p.communicate();

        taggerName = "--".join(self._stripTagDir(tagger).split("/"))
        logFilename = \
            os.path.join("Contents", "Logs",
                         "%03d--%s.log" % (self.logFileNumber, taggerName))
        self.logFileNumber += 1;

        taggingLog = None
        taggingError = None
        
        with open(logFilename, "w") as f:
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
            f.write(tagData)
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
                    taggingLog = simplejson.loads(tagData)
                except ValueError, e:
                    taggingError = ("error parsing output of tagger '%s':\n%s" %
                                    (self._stripTagDir(tagger), e))
                    print >>f
                    print >>f
                    print >>f, "=== Error parsing tag data"
                    print >>f
                    print >>f, str(e)
            else:
                taggingError = ("error running tagger '%s':\n%s" %
                                (self._stripTagDir(tagger), errors))
                print >>f, "=== Process failed: return code %d" % p.returncode
                                
        if taggingError:
            self.logger.error(taggingError)
            self.addFile(logFilename)
            self.addTagRef("error--tagger failed", path=logFilename, 
                           context="snapshot--" + self.sessionInfo["id"])
            return
            
        for entry in taggingLog:
            tag = entry["tag"]
            if tag.startswith("file--"):
                self.addFileTagRef(tag[6:])
            else:
                try:
                    filename, _, lineNum = entry["location"].partition(":")
                except KeyError:
                    filename = lineNum = None

                properties = dict()
                if "sort_name" in entry:
                    properties["sortName"] = entry["sort_name"]
                if "display_name" in entry:
                    properties["displayName"] = entry["display_name"]
                if "implied_by" in entry:
                    properties["context"] = entry["implied_by"]
                self.addTagRef(tag, taggerName, filename, lineNum, properties)

                if "implies" in entry:
                    self.addTagRef(entry["implies"], taggerName, filename,
                                   lineNum, context=tag)

    def makePackageStructure(self):
        dirs = (
            "Contents",
            "Contents/Logs",
            "Contents/Resources",
            )
        for dir in dirs:
            if not os.path.exists(dir): os.mkdir(dir)
        with open("Contents/PkgInfo", "w") as f:
            f.write("????????")


    def activelyGenerateTags(self):
        si = self.sessionInfo = dict(
            id = base64.encodestring(uuid.uuid4().bytes)[:-3],
            timestamp = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            device = self.session.device,
            user = self.session.user,
            osName = self.session.os_name,
            )
        s = "\n".join("%s=%s" % (k, si[k]) for k in sorted(si))
        self.addFileTagRef("sessionInfo", s)

        self.addFileTagRef("login.log", self.session.login_info)

        while self.pendingCommands:
            command, filename = self.pendingCommands.pop()
            assert not os.path.exists(filename)
            content = self.session.perform_command(command)
            if content:
                self.addFileTagRef(filename, content)

    def passivelyGenerateTags(self):
        if not os.path.exists("sessionInfo"):
            raise error("sessionInfo file not found")

        si = self.sessionInfo = {}
        with open("sessionInfo") as f:
            for line in f:
                k, _, v = line.partition("=")
                si[k.strip()] = v.strip()
        for name in self.interestingFiles():
            self.addFileTagRef(name)

    def interestingFiles(self):
        for name in os.listdir("."):
            if name.startswith(".") or name.endswith("~") \
                    or name in ("Contents", "pexpect.log"):
                continue
            yield name

    def syntaxHighlightFile(self, filename, *syntaxes):
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

        outFilename = os.path.join("Contents", "Resources", filename + ".html")
        outDir = os.path.dirname(outFilename)
        if not os.path.isdir(outDir):
            os.makedirs(outDir)
        with open(outFilename, "w") as f:
            result = pygments.highlight(content, lexer, formatter, f)

    def syntaxHighlightFiles(self):
        for filename in self.interestingFiles():
            file_tag = "file--" + filename
            if file_tag not in self.tagRefs:
                self.logger.warning("creating missing file tag for '%s'",
                                    filename)
                self.addFileTagRef(filename)

            ancestors = set()
            tocheck = set()
            tocheck.add(file_tag)
            while tocheck:
                for tag_ref in self.tagRefs[tocheck.pop()]:
                    if "context" not in tag_ref: continue
                    context_tag = tag_ref["context"]
                    if context_tag not in ancestors \
                            and not context_tag.startswith("snapshot--"):
                        ancestors.add(context_tag)
                        tocheck.add(context_tag)

            syntaxes = [t.partition("--")[0] for t in ancestors]
            self.logger.debug("for file '%s' found syntaxes %r",
                    filename, syntaxes)

            self.syntaxHighlightFile(filename, *syntaxes)


    def generateTags(self):
        self.loadTagDir('internal--startup', self.taggersDir)

        if self.session:
            self.activelyGenerateTags()
        else:
            self.passivelyGenerateTags()

        self.syntaxHighlightFiles()


    def getTagNamesByKind(self, kind):
        matches = set(t for t in self.tagRefs if t.startswith(kind + "--"))
        return [tag.partition("--")[2] for tag in matches]

    def getTagNameByKind(self, kind):
        names = self.getTagNamesByKind(kind)
        return names[0] if names else None

    def writeInfoPlist(self):
        unreferencedTags = [k for k, v in self.tagRefs.iteritems() if not v]
        for tag in unreferencedTags:
            del self.tagRefs[tag]

        ts = datetime.datetime.strptime(self.sessionInfo["timestamp"],
                                       "%Y-%m-%dT%H:%M:%S")
        user = self.getTagNameByKind("config user")
        log = self.getTagNameByKind("config log")

        info = dict()
        info["tags"] = self.tagRefs
        info["device"] = self.sessionInfo["device"]
        info["snapshotID"] = self.sessionInfo["id"]
        info["timestamp"] = ts
        if user: info["user"] = user
        if log: info["log"] = log

        plist = os.path.join("Contents", "Info.plist")
        plistlib.writePlist(info, plist)
        
        info["timestamp"] = self.sessionInfo["timestamp"]
        with open(os.path.join("Contents", "info.json"), "w") as f:
            simplejson.dump(info, f, sort_keys=True, indent=2)
