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
Canner
"""

__author__ = "!j Incorporated"

from setuptools import setup
setup(
    name = "Canner",
    version = "0.1",
    description = __doc__,
    author = __author__,

    provides = ["Canner"],
    requires = ["Pygments (>=0.9)",
                "pexpect (>=2.1)",
                "lxml (>=1.3)",
                "IPy (>=0.55)",
                ],

    packages = ["canner",
                "canner.syntax",
                "canner.personalities",
                "tests",
                ],

    test_suite = "tests.suite",

    entry_points = {
        "console_scripts": [
            "canner = canner.cmdline:main",
            ],
            
        "pygments.lexers": [
            "ios = canner.syntax:IosLexer",
            "junos = canner.syntax:JunosLexer",
            ],
        "pygments.formatters": [
            "CannerHTML = canner.syntax:CannerHtmlFormatter",
            ]
        },
    )
