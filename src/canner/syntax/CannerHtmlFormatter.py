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

# $Id$

import re
import pygments.formatters.html
from pygments.formatters import HtmlFormatter

HEADER = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
   "http://www.w3.org/TR/html4/strict.dtd">

<html>
<head>
  <script language="javascript" type="text/javascript">
    if (baseOverride) {
      var obj = document.createElement('BASE');
      obj.href = baseOverride;
      document.getElementsByTagName('HEAD')[0].appendChild(obj);
    }
  </script>

  <title>%(title)s</title>
  <meta http-equiv="content-type" content="text/html; charset=%(encoding)s">
  <link rel="stylesheet" href="%(cssfile)s" type="text/css">
</head>
<body>
'''

LINENOS = '''\
body {
    counter-reset: line;
    margin: 0;
    font-size: 9pt;
}

.gutter:before {
    display: inline-block;
    width: 3em;
    overflow: hidden;
    margin-right: 4pt;
    background: rgb(200,200,200);
    padding: 1px 3px 1px 0;
    border-right: thin solid black;
    font-family: Helvetica;
    font-size: 8pt;
    text-align: right;
    content: "  ";
    -webkit-user-select: none;
}

.code {
    white-space: pre;
    font-family: Courier;
}
.code:before {
    content: counter(line);
    counter-increment: line;
}

.diffadd {
    background: #9F9;
}

.diffchg {
    background: #FF9;
}

.diffins {
    background: #F99;
}
'''

pygments.formatters.html.DOC_HEADER_EXTERNALCSS = HEADER

class CannerHtmlFormatter(HtmlFormatter):
    """
    FIXME: help should go here
    """
    name = 'Canner HTML'
    aliases = ['canner']
    filenames = ['*.html']

    def _wrap_inlinelinenos(self, inner):
        num = 1
        for t, line in inner:
            yield 1, '<div id="line-%d" class="code gutter">' % num + line.rstrip('\n') + '</div>\n'
            num += 1

    def wrap(self, source, outfile):
        return source

    def get_style_defs(self, arg):
        return LINENOS + HtmlFormatter.get_style_defs(self, arg)
