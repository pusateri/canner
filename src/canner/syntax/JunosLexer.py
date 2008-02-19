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

from pygments.lexer import RegexLexer
from pygments.token import *

class JunosLexer(RegexLexer):
    """
    FIXME: help should go here
    """
    name = 'Juniper Networks JUNOS'
    aliases = ['junos']
    filenames = ['*.conf']
    tokens = {
        'root': [
            (r'/\*', Comment.Multiline, 'comment'),
            (r'//.*?$', Comment.Singleline),
            (r'#.*?$', Comment.Singleline),
            (r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?', Number),
            (r'(([\dA-Fa-f]{1,4}\:{1,2})|\:{2,2})([\dA-Fa-f]{1,4}\:{1,2}){0,6}[\dA-Fa-f]{1,4}(\/\d{1,3})?', Number),
            (r'{', Punctuation),
            (r'}', Punctuation),
            (r';', Punctuation),
            (r'\[', Punctuation),
            (r'\]', Punctuation),
            (r'/', Punctuation),
            (r'(version|system|protocols|interfaces|snmp|routing-options|'
             r'policy-options|groups|apply-groups|login|user|'
             r'services|ntp|unit|family|address|community|authorization|'
             r'rib|static|route|next-hop|retain|igmp|ospf|ospf3|'
             r'pim|rip|export|neighbor|flag|file|size|files|interface|'
             r'mode|priority|host-name|domain-name|time-zone|'
             r'location|root-authentication|encrypted-password|'
             r'full-name|uid|class|authentication|ssh-dsa|ssh-rsa|'
             r'boot-server|server|inet|inet6|group|traceoptions|'
             r'policy-statement|from|then|accept|direct|name-server|'
             r'ssh|telnet|xnm-clear-text|altitude|building|'
             r'country-code|floor|hcoord|lata|latitude|longitude|'
             r'npa-nxx|postal-code|rack|vcoord|term|protocol|packets|'
             r'error|world-readable|sparse|all|read-write|operator|'
             r'read-only|super-user|unauthorized|permissions|'
             r'forwarding-options|helpers|bootp|ripng|radius-server|'
             r'secret|admin|clear|configure|floppy|network|reset|'
             r'routing|shell|trace|view|maintenance|firewall|'
             r'rollback|security|authentication-order|radius|'
             r'password|area|netconf)(?=\s+)', Keyword),
            (r'"', String.Double, 'string'),
            (r'\s+', Text),
            (r'\w[\w\.-]*[\w]+', Text),
            (r'\d+', Number),
        ],
        'comment': [
            (r'[^*/]', Comment.Multiline),
            (r'/\*', Comment.Multiline, '#push'),
            (r'\*/', Comment.Multiline, '#pop'),
            (r'[*/]', Comment.Multiline)
        ],
        'string': [
            (r'.*"', String.Double, '#pop')
        ]
    }
