#!/usr/bin/python

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

import os
import signal
import sys
import logging
import shlex
import shutil
import datetime
import traceback
import subprocess
from optparse import OptionParser

from . import error
from .session import Session
from .engine import Engine


def add_options(parser):

    # modes

    parser.add_option('-i', '--interact', dest='interact',
                      action="store_true",
                      help="connect to a device and interact with it")
    parser.add_option('-r', '--retag', dest='retag',
                      action="store_true",
                      help="retag an existing snapshot")
    parser.set_defaults(interact=False, retag=False)

    # verbosity and logging

    parser.add_option("-q", "--quiet", dest="verbosity", 
                      action="store_const", const=30),
    parser.add_option("-v", "--verbose", dest="verbosity", 
                      action="store_const", const=10),
    parser.add_option('-l', '--log', dest='log_session', action='store_true', 
                      help='enable logging')
    parser.set_defaults(verbosity=20, log=False)

    # initialization (RC files)

    parser.add_option("--norc", dest="use_canner_rc", action="store_false",
                      help="ignore rc files")
    parser.add_option("--rcfile", dest="rc_files", action="append",
                      help="use FILE instead of default rc file")
    parser.add_option("--oneshotrc", dest="oneshot_rc_files", action="append",
                      help="use FILE as an rc file and then delete it")
    parser.set_defaults(use_canner_rc=True, rc_files=[], oneshot_rc_files=[])

    # environment

    parser.add_option('-t', '--taggersdir', dest='taggers_dir',
                      help='load taggers from DIR', metavar='DIR')
    parser.add_option('-s', '--snapshotsdir', dest='snapshots_dir',
                      help='store snapshot in DIR', metavar='DIR')

    # snapshot file control

    parser.add_option("-n", "--name", dest="snapname", action="store",
                      help="filename to use for the snapshot")
    parser.add_option('-o', '--organize', dest='organize', action='store_true',
                      help='automatically orgainze the snapshot')
    parser.add_option("-f", "--force", dest="force", action="store_true",
                      help="overwrite snapshot if one already exists")
    parser.set_defaults(organize=False, force=False)

    # session parameters

    parser.add_option('-c', '--connect', dest='connect_command',
                      help='command used to connect to the device')
    parser.add_option('-u', '--user', dest='user',
                      help='login USER')
    parser.add_option('-p', '--password', dest='password',
                      help='login PASSWORD')
    parser.add_option('-e', '--exec-password', dest='exec_password', 
                      help='exec PASSWORD')
    parser.add_option("-T", "--timeout", dest="timeout", type="int")

    # interfacing with other programs

    parser.add_option('--on-success', dest='on_success',
                      help='command to run if canning is successful')


def process_options(parser, options, args):

    handler = logging.StreamHandler()
    handler.setLevel(options.verbosity)
    if options.verbosity >= logging.INFO:
        format = "%(levelname)-8s %(message)s"
    else:
        format = "%(asctime)s %(levelname)-8s %(message)s"
    handler.setFormatter(logging.Formatter(format))
    logging.getLogger("").addHandler(handler)
    logging.getLogger("").setLevel(options.verbosity)

    options.rc_files = [os.path.expanduser(p) for p in options.rc_files]
    options.oneshot_rc_files = [os.path.expanduser(p) 
                                for p in options.oneshot_rc_files]
    if options.oneshot_rc_files:
        options.rc_files = options.oneshot_rc_files + options.rc_files
    if options.rc_files and not options.use_canner_rc:
        parser.error("--norc cannot be used with --rcfile or --oneshotrc")

    if options.snapname:
        if options.organize:
            paser.error("a snapshot name cannot be specified in organize mode")
        if options.interact:
            paser.error("a snapshot name cannot be specified in interact mode")
        if options.retag:
            paser.error("a snapshot name cannot be specified in retag mode")

    if len(args) != 1:
        thing = "snapshot" if options.retag else "device"
        parser.error("a %s is required" % thing)
    
    if not options.taggers_dir:
        options.taggers_dir = os.environ.get('TAGGERS_DIR', None)
    if not options.taggers_dir:
        dir = os.path.expanduser('~/Taggers')
        if os.path.isdir(dir):
            options.taggers_dir = dir
    if not options.taggers_dir:
        my_dir = os.path.dirname(os.path.abspath(__file__))
        options.taggers_dir = os.path.normpath(
            os.path.join(my_dir, '..', 'taggers'))
    if not options.taggers_dir:
        dir = os.path.expanduser('/usr/local/share/netCannery/taggers')
        if os.path.isdir(dir):
            options.taggers_dir = dir
    if not options.taggers_dir:
        parser.error('could not determine taggers directory')

    if options.organize:
        if options.interact:
            parser.error("organize cannot be used with interact")
        if options.retag:
            parser.error("organize cannot be used with retag")
        if not options.snapshots_dir:
            options.snapshots_dir = os.environ.get('SNAPSHOTS_DIR', None)
        if not options.snapshots_dir:
            nc = os.path.expanduser('~/Library/Application Support/netCannery')
            if os.path.isdir(nc):
                options.snapshots_dir = os.path.join(nc, 'Snapshots', 
                                                        'Canned Locally')
                if not os.path.isdir(options.snapshots_dir):
                    os.makedirs(options.snapshots_dir)
        if not options.snapshots_dir:
            dir = os.path.expanduser('~/Snapshots')
            if os.path.isdir(dir):
                options.snapshots_dir = dir
        if not options.snapshots_dir:
            parser.error('could not determine snapshots directory')
    else:
        if options.snapshots_dir:
            parser.error('snapshots dir invalid when not in organize mode')
    
    if options.on_success:
        if options.interact:
            parser.error("on-success cannot be used with interact")

    return options, args


def start_debug_logging():
    if not os.path.exists("Contents/Logs"):
         os.makedirs("Contents/Logs")
    fh = logging.FileHandler("Contents/Logs/Canner.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(name)-12s: %(levelname)-8s %(message)s"))
    logging.getLogger("").addHandler(fh)
    logging.getLogger("").setLevel(logging.DEBUG)
    

def create_session(device, options):
    session = Session(device=device, 
                      user=options.user, 
                      password=options.password, 
                      exec_password=options.exec_password, 
                      command=options.connect_command,
                      should_log=options.log_session,
                      use_rc_files=options.use_canner_rc,
                      rc_files=options.rc_files)
    if options.timeout:
        session.timeout = options.timeout

    for rcfile in options.oneshot_rc_files:
        os.remove(rcfile)

    return session


def run_hook(command, pkgdir):
    args = shlex.split(command)
    if '{}' in command:
        for idx, arg in enumerate(args):
            args[idx] = arg.replace('{}', pkgdir)
    logging.debug('running hook: %r' % args)
    retcode = subprocess.call(args)
    if retcode != 0:
        logging.error('failed to run hook: %d: %r' % (retcode, args))


def interact(options, device):
    session = create_session(device, options)
    session.start(login_only=True)
    logging.info("session established")
    session.interact()


def retag(options, pkg):
    starting_dir = os.getcwd()
    pkgdir = os.path.join(starting_dir, pkg)
    if not os.path.isdir(pkgdir):
        raise error("snapshot directory '%s' not found" % pkgdir)

    os.chdir(pkgdir)
    if os.path.exists("Contents"):
        shutil.rmtree("Contents")

    start_debug_logging()
    logging.info("snapshot: %s", pkgdir)

    engine = Engine(options.taggers_dir)
    engine.run()

    if options.on_success:
        os.chdir(starting_dir)
        run_hook(options.on_success, pkgdir)


def can(options, device):
    starting_dir = os.getcwd()
    snapshots_dir = options.snapshots_dir or starting_dir
    os.chdir(snapshots_dir)

    timestamp = datetime.datetime.utcnow()

    if options.snapname:
        pkg = options.snapname
    elif options.organize:
        ts = timestamp.strftime
        basedir = ts('%Y/%m/%d')
        if not os.path.isdir(basedir):
            os.makedirs(basedir)
        os.chdir(basedir)
        pkg = '%s--%s.netcan' % (device, ts('%Y-%m-%d-%H-%M-%S'))
    else:
        pkg = "%s.netcan" % device

    if os.path.isdir(pkg) and not options.force:
        raise error("snapshot directory '%s' already exists" % pkg)

    if os.path.exists(pkg):
        shutil.rmtree(pkg)
    os.mkdir(pkg)
    os.chdir(pkg)
    pkgdir = os.getcwd()

    start_debug_logging()
    logging.info("snapshot: %s", pkgdir)

    session = create_session(device, options)
    try:
        session.start()
        engine = Engine(options.taggers_dir, session, timestamp)
        engine.run()
    except Exception:
        exc_info = sys.exc_info()
        logging.error("caught error, attempting to close session")
        try:
            session.close()
        except Exception, e:
            logging.error("ignoring error cleaning up session: " + str(e))
        raise exc_info[0], exc_info[1], exc_info[2]
    else:
        session.close()
        if options.on_success:
            os.chdir(starting_dir)
            run_hook(options.on_success, pkgdir)

        
def log_exception():
    """
    Log the usual traceback information, followed by a listing of all the
    local variables in each frame.
    
    Inspired by http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52215
    """

    logging.debug(traceback.format_exc())
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack = []
    while exc_traceback:
        stack.append(exc_traceback.tb_frame)
        exc_traceback = exc_traceback.tb_next
        
    buf = []
    buf.append("Locals by frame (most recent call last):")
    for fr in stack:
        buf.append("Frame '%s' in '%s' at line %s" % (fr.f_code.co_name,
                                                      fr.f_code.co_filename,
                                                      fr.f_lineno))
        for key, value in fr.f_locals.items():
            try:                   
                buf.append("    %s = %s" % (key, repr(value)))
            except:
                buf.append("    %s = <ERROR FORMATTING VALUE>" % key)
        buf.append("")
    logging.debug("\n".join(buf[:-1]))

    logging.error("\n".join(traceback.format_exception_only(exc_type, 
                                                            exc_value)))


def main():
    def force_quit(signum, frame):
        raise error("caught signal %d" % signum)
    signal.signal(signal.SIGTERM, force_quit)
    
    try:
        usage = 'usage: %prog [options] device'
        parser = OptionParser(usage)
        add_options(parser)
        options, args = parser.parse_args()
        process_options(parser, options, args)

        if options.interact:
            interact(options, args[0])
        elif options.retag:
            retag(options, args[0])
        else:
            can(options, args[0])

    except SystemExit:
        pass
        
    except KeyboardInterrupt:
        sys.exit(1)
        
    except:
        log_exception()
        sys.exit(1)

            
if __name__ == '__main__':
    main()

