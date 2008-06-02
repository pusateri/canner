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

"""
Canner is an open source framework for talking to network devices from
a variety of vendors. Arbitrary commands can be issued to the device
and the raw output and logs are saved in files in a directory snapshot
or 'can'. Canner extracts specific, targeted information in a
device-dependent manner to highlight the details of the network that
are of interest to its operators.
"""

__author__ = "!j Incorporated"

import ez_setup
ez_setup.use_setuptools("0.6c8")

from setuptools import setup

setup(
    name = "Canner",
    version = "0.2",
    author = __author__,
    author_email = "support@bang.com",
    url = "canner.bangj.com",
    description = \
        "A tool for snapshotting and parsing network device configuration",
    long_description = __doc__,
    
    provides = ["Canner"],

    install_requires = ["Pygments >=0.9",
                        "pexpect >=2.1",
                        "lxml >=1.3, <2a",
                        "IPy ==0.56",
                        "simplejson >=1.7",
                        "Genshi >=0.4",
                        ],

    packages = ["canner",
                "canner.syntax",
                "canner.personalities",
                ],

    test_suite = "tests.suite",

    zip_safe = True,

    entry_points = {
        "console_scripts": [
            "canner = canner.cmdline:main",
            ],

        "canner.personalities": [
            "bootstrap = canner.personalities.bootstrap:BootstrapPersonality",
            "dell = canner.personalities.dell:DellPersonality",
            "extreme_xos = canner.personalities.extreme_xos:ExtremeXOSPersonality",
            "extremeware = canner.personalities.extremeware:ExtremeWarePersonality",
            "freebsd = canner.personalities.freebsd:FreeBSDPersonality",
            "hp_procurve = canner.personalities.hp_procurve:HPProCurvePersonality",
            "ios = canner.personalities.ios:IOSPersonality",
            "ios_xr = canner.personalities.ios_xr:IOSXRPersonality",
            "junos = canner.personalities.junos:JUNOSPersonality",
            "netbsd = canner.personalities.netbsd:NetBSDPersonality",
            "netgear = canner.personalities.netgear:NETGEARPersonality",
            "netscreen = canner.personalities.netscreen:NetscreenPersonality",
            "openbsd = canner.personalities.openbsd:OpenBSDPersonality",
            "procket = canner.personalities.procket:ProcketPersonality",
            "smc = canner.personalities.smc:SMCPersonality",
            ],
            
        "pygments.lexers": [
            "ios = canner.syntax:IosLexer",
            "ios_xr = canner.syntax:IosXRLexer",
            "junos = canner.syntax:JunosLexer",
            ],
        "pygments.formatters": [
            "CannerHTML = canner.syntax:CannerHtmlFormatter",
            ]
        },
    )
