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

from pygments.lexer import RegexLexer, bygroups, include
from pygments.token import *
import IPy

class IosLexer(RegexLexer):
    """
    FIXME: help should go here
    """
    name = 'Cisco Systems IOS'
    aliases = ['ios']
    filenames = ['*.cfg']

    tokens = {
        'root': [
            (r'(?s)\A[^!]+', Generic.Output),
            (r'\n', Text),
            (r'!.*', Comment),
            include('commands'),
            (r'end(?=\s)', Keyword),
            ],

        'commands': [
            (r'^\s+', Error),
            (r'\s', Text),
            (r'no(?=\s)', Operator.Word),
            (r'aaa(?=\s)', Keyword, 'aaa'),
            (r'access-list(?=\s)', Keyword, 'acl'),
            (r'banner(?=\s)', Keyword, ('slurp', 'litHeredoc', 'litKeyword')),
            (r'boot(?=\s)', Keyword, 'slurp'),
            (r'boot-start-marker(?=\s)', Keyword, 'slurp'),
            (r'boot-end-marker(?=\s)', Keyword, 'slurp'),
            (r'bridge(?=\s)', Keyword, 'slurp'),
            (r'call(?=\s)', Keyword, 'slurp'),
            (r'cdp(?=\s)', Keyword, 'slurp'),
            (r'clock(?=\s)', Keyword, 'slurp'),
            (r'cluster(?=\s)', Keyword, 'slurp'),
            (r'control-plane(?=\s)', Keyword, 'slurp'),
            (r'crypto(?=\s)', Keyword, ('crypto', 'slurp')),
            (r'dial-peer(?=\s)', Keyword, 'slurp'),
            (r'dot11(?=\s)', Keyword, 'dot11'),
            (r'enable(?=\s)', Keyword, 'slurp'),
            (r'exception(?=\s)', Keyword, 'slurp'),
            (r'file(?=\s)', Keyword, 'slurp'),
            (r'hostname(?=\s)', Keyword, 'litString'),
            (r'interface(?=\s)', Keyword, ('interface', 'litInterfaceName')),
            (r'ip(?=\s)', Keyword, 'ip'),
            (r'ipv6(?=\s)', Keyword, 'ip'),
            (r'line(?=\s)', Keyword, ('line', 'slurp')),
            (r'logging(?=\s)', Keyword, 'logging'),
            (r'mmi(?=\s)', Keyword, 'slurp'),
            (r'mpls(?=\s)', Keyword, 'slurp'),
            (r'ntp(?=\s)', Keyword, 'ntp'),
            (r'power(?=\s)', Keyword, 'slurp'),
            (r'prompt(?=\s)', Keyword, 'litString'),
            (r'resource(?=\s)', Keyword, 'slurp'),
            (r'radius-server(?=\s)', Keyword, 'radius'),
            (r'router(?=\s)', Keyword, 'router'),
            (r'scheduler(?=\s)', Keyword, 'slurp'),
            (r'service(?=\s)', Keyword, 'slurp'),
            (r'snmp(?=\s)', Keyword, 'slurp'),
            (r'snmp-server(?=\s)', Keyword, 'snmp-server'),
            (r'sntp(?=\s)', Keyword, 'slurp'),
            (r'spanning-tree(?=\s)', Keyword, 'slurp'),
            (r'system(?=\s)', Keyword, 'slurp'),
            (r'tacacs-server(?=\s)', Keyword, 'slurp'),
            (r'username(?=\s)', Keyword, 'username'),
            (r'version(?=\s)', Keyword, 'litBareWord'),
            (r'vlan(?=\s)', Keyword, 'vlan'),
            (r'vtp(?=\s)', Keyword, 'slurp'),
            (r'wlccp(?=\s)', Keyword, 'slurp'),
            ],

        'aaa': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'accounting(?=\s)', Keyword, 'slurp'),
            (r'authentication(?=\s)', Keyword, 'slurp'),
            (r'authorization(?=\s)', Keyword, 'slurp'),
            (r'cache(?=\s)', Keyword, ('#pop', 'aaa cache', 'slurp')),
            (r'group(?=\s)', Keyword, ('#pop', 'aaa group', 'slurp')),
            (r'new-model(?=\s)', Keyword, 'slurp'),
            (r'session-id(?=\s)', Keyword, 'slurp'),
            ],

        'aaa cache': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'all(?=\s)', Keyword),
            (r'cache(?=\s)', Keyword, 'slurp'),
            (r'domain(?=\s)', Keyword, 'slurp'),
            (r'no(?=\s)', Operator.Word),
            (r'password(?=\s)', Keyword, 'slurp'),
            ],
            
        'aaa group': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'server(?=\s)', Keyword, 'slurp'),
            (r'cache(?=\s)', Keyword, 'slurp'),
            ],

        'crypto': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            ],
            
        'dot11': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'ids(?=\s)', Keyword, 'slurp'),
            (r'ssid(?=\s)', Keyword, ('#pop', 'dot11 ssid', 'litString')),
            (r'vlan-name(?=\s)', Keyword, ('#pop', 'litInteger', 'litKeyword', 'litString')),
            (r'wpa(?=\s)', Keyword, 'slurp'),
            ],

        'dot11 ssid': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'authentication(?=\s)', Keyword, 'slurp'),
            (r'max-associations(?=\s)', Keyword, 'litInteger'),
            (r'mbssid(?=\s)', Keyword, 'slurp'),
            (r'no(?=\s)', Operator.Word),
            (r'vlan(?=\s)', Keyword, 'litInteger'),
            ],

        'interface': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'!.*', Comment),
            (r'no(?=\s)', Operator.Word),
            (r'arp(?=\s)', Keyword, 'slurp'),
            (r'bandwidth(?=\s)', Keyword, 'slurp'),
            (r'bridge-group(?=\s)', Keyword, 'slurp'),
            (r'carrier-delay(?=\s)', Keyword, 'slurp'),
            (r'cdp(?=\s)', Keyword, 'slurp'),
            (r'channel(?=\s)', Keyword, 'slurp'),
            (r'clns(?=\s)', Keyword, 'slurp'),
            (r'crc(?=\s)', Keyword, 'slurp'),
            (r'custom-queue-list(?=\s)', Keyword, 'slurp'),
            (r'delay(?=\s)', Keyword, 'slurp'),
            (r'description(?=\s)', Keyword, 'litStringEOL'),
            (r'dfs(?=\s)', Keyword, 'slurp'),
            (r'duplex(?=\s)', Keyword, 'slurp'),
            (r'encapsulation(?=\s)', Keyword, 'slurp'),
            (r'encryption(?=\s)', Keyword, 'slurp'),
            (r'fair-queue(?=\s)', Keyword, 'slurp'),
            (r'half-duplex(?=\s)', Keyword, 'slurp'),
            (r'hold-queue(?=\s)', Keyword, 'slurp'),
            (r'ip(?=\s)', Keyword, 'ip'),
            (r'ipv6(?=\s)', Keyword, 'ip'),
            (r'keepalive(?=\s)', Keyword, 'slurp'),
            (r'load-interval(?=\s)', Keyword, 'slurp'),
            (r'logging(?=\s)', Keyword, 'slurp'),
            (r'loopback(?=\s)', Keyword, 'slurp'),
            (r'mbssid(?=\s)', Keyword, 'slurp'),
            (r'mac-address(?=\s)', Keyword, 'slurp'),
            (r'management(?=\s)', Keyword, 'slurp'),
            (r'max-reserved-bandwidth(?=\s)', Keyword, 'slurp'),
            (r'mop(?=\s)', Keyword, 'slurp'),
            (r'mtu(?=\s)', Keyword, 'slurp'),
            (r'ntp(?=\s)', Keyword, 'ntp'),
            (r'pos(?=\s)', Keyword, 'slurp'),
            (r'power(?=\s)', Keyword, 'slurp'),
            (r'priority-group(?=\s)', Keyword, 'slurp'),
            (r'random-detect(?=\s)', Keyword, 'slurp'),
            (r'rate-limit(?=\s)', Keyword, 'slurp'),
            (r'rmon(?=\s)', Keyword, 'slurp'),
            (r'serial(?=\s)', Keyword, 'slurp'),
            (r'service-policy(?=\s)', Keyword, 'slurp'),
            (r'speed(?=\s)', Keyword, 'slurp'),
            (r'shutdown(?=\s)', Keyword, 'slurp'),
            (r'snmp(?=\s)', Keyword, 'slurp'),
            (r'spanning-tree(?=\s)', Keyword, 'slurp'),
            (r'ssid(?=\s)', Keyword, 'litString'),
            (r'standby(?=\s)', Keyword, 'slurp'),
            (r'station-role(?=\s)', Keyword, 'slurp'),
            (r'switchport(?=\s)', Keyword, 'slurp'),
            (r'timeout(?=\s)', Keyword, 'slurp'),
            (r'transmit-interface(?=\s)', Keyword, 'slurp'),
            (r'tx-queue-limit(?=\s)', Keyword, 'slurp'),
            (r'udld(?=\s)', Keyword, 'slurp'),
            (r'world-mode(?=\s)', Keyword, 'slurp'),
            ],

        'ip': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'access-group(?=\s)', Keyword, 'ip access-group options'),
            (r'access-list(?=\s)', Keyword, 'acl'),
            (r'accounting(?=\s)', Keyword, 'slurp'),
            (r'accounting-list(?=\s)', Keyword, 'slurp'),
            (r'accounting-threshold(?=\s)', Keyword, 'slurp'),
            (r'accounting-transits(?=\s)', Keyword, 'slurp'),
            (r'address(?=\s)', Keyword, 'ip-address'),
            (r'address-pool(?=\s)', Keyword, 'slurp'),
            (r'alias(?=\s)', Keyword, 'slurp'),
            (r'as-path(?=\s)', Keyword, 'slurp'),
            (r'authentication(?=\s)', Keyword, 'slurp'),
            (r'bandwidth-percent(?=\s)', Keyword, 'slurp'),
            (r'bgp(?=\s)', Keyword, 'slurp'),
            (r'bgp-community(?=\s)', Keyword, 'slurp'),
            (r'bootp(?=\s)', Keyword, 'slurp'),
            (r'broadcast-address(?=\s)', Keyword, 'slurp'),
            (r'cef(?=\s)', Keyword, 'slurp'),
            (r'cgmp(?=\s)', Keyword, 'slurp'),
            (r'classless(?=\s)', Keyword, 'slurp'),
            (r'community-list(?=\s)', Keyword, 'slurp'),
            (r'default-gateway(?=\s)', Keyword, 'slurp'),
            (r'default-network(?=\s)', Keyword, 'slurp'),
            (r'dhcp(?=\s)', Keyword, 'slurp'),
            (r'dhcp-client(?=\s)', Keyword, 'slurp'),
            (r'dhcp-server(?=\s)', Keyword, 'slurp'),
            (r'directed-broadcast(?=\s)', Keyword, 'slurp'),
            (r'domain-list(?=\s)', Keyword, 'litBareWord'),
            (r'domain(-|\s)lookup(?=\s)', Keyword, 'slurp'),
            (r'domain(-|\s)name(?=\s)', Keyword, 'litBareWord'),
            (r'drp(?=\s)', Keyword, 'slurp'),
            (r'dvmrp(?=\s)', Keyword, 'slurp'),
            (r'extcommunity-list(?=\s)', Keyword, 'slurp'),
            (r'finger(?=\s)', Keyword, 'slurp'),
            (r'flow(?=\s)', Keyword, 'slurp'),
            (r'flow-aggregation(?=\s)', Keyword, 'slurp'),
            (r'flow-cache(?=\s)', Keyword, 'slurp'),
            (r'flow-export(?=\s)', Keyword, 'slurp'),
            (r'forward-protocol(?=\s)', Keyword, 'slurp'),
            (r'ftp(?=\s)', Keyword, 'slurp'),
            (r'gdp(?=\s)', Keyword, 'slurp'),
            (r'gratuitous-arps(?=\s)', Keyword, 'slurp'),
            (r'hello-interval(?=\s)', Keyword, 'slurp'),
            (r'helper-address(?=\s)', Keyword, 'litAddress'),
            (r'hold-time(?=\s)', Keyword, 'slurp'),
            (r'host(?=\s)', Keyword, 'slurp'),
            (r'host-routing(?=\s)', Keyword, 'slurp'),
            (r'hp-host(?=\s)', Keyword, 'slurp'),
            (r'http(?=\s)', Keyword, 'http'),
            (r'icmp(?=\s)', Keyword, 'slurp'),
            (r'idle-group(?=\s)', Keyword, 'slurp'),
            (r'igmp(?=\s)', Keyword, 'slurp'),
            (r'irdp(?=\s)', Keyword, 'slurp'),
            (r'load-sharing(?=\s)', Keyword, 'slurp'),
            (r'local(?=\s)', Keyword, 'slurp'),
            (r'local-proxy-arp(?=\s)', Keyword, 'slurp'),
            (r'mask-reply(?=\s)', Keyword, 'slurp'),
            (r'mrm(?=\s)', Keyword, 'slurp'),
            (r'mroute(?=\s)', Keyword, 'slurp'),
            (r'mroute-cache(?=\s)', Keyword, 'slurp'),
            (r'msdp(?=\s)', Keyword, 'slurp'),
            (r'mtu(?=\s)', Keyword, 'slurp'),
            (r'multicast(?=\s)', Keyword, 'slurp'),
            (r'multicast-routing(?=\s)', Keyword, 'slurp'),
            (r'name-server(?=\s)', Keyword, 'litAddress'),
            (r'nat(?=\s)', Keyword, 'slurp'),
            (r'nbar(?=\s)', Keyword, 'slurp'),
            (r'nhrp(?=\s)', Keyword, 'slurp'),
            (r'ospf(?=\s)', Keyword, 'slurp'),
            (r'pgm(?=\s)', Keyword, 'slurp'),
            (r'pim(?=\s)', Keyword, 'slurp'),
            (r'policy(?=\s)', Keyword, 'slurp'),
            (r'policy-list(?=\s)', Keyword, 'slurp'),
            (r'prefix-list(?=\s)', Keyword, 'slurp'),
            (r'proxy-arp(?=\s)', Keyword, 'slurp'),
            (r'radius(?=\s)', Keyword, 'slurp'),
            (r'rarp-server(?=\s)', Keyword, 'slurp'),
            (r'rcmd(?=\s)', Keyword, 'slurp'),
            (r'redirects(?=\s)', Keyword, 'slurp'),
            (r'reflexive-list(?=\s)', Keyword, 'slurp'),
            (r'rgmp(?=\s)', Keyword, 'slurp'),
            (r'rip(?=\s)', Keyword, 'slurp'),
            (r'route(?=\s)', Keyword, 'ip-route'),
            (r'route-cache(?=\s)', Keyword, 'slurp'),
            (r'routing(?=\s)', Keyword, 'slurp'),
            (r'rsvp(?=\s)', Keyword, 'slurp'),
            (r'rtcp(?=\s)', Keyword, 'slurp'),
            (r'rtp(?=\s)', Keyword, 'slurp'),
            (r'sap(?=\s)', Keyword, 'slurp'),
            (r'scp(?=\s)', Keyword, 'scp'),
            (r'security(?=\s)', Keyword, 'slurp'),
            (r'split-horizon(?=\s)', Keyword, 'slurp'),
            (r'source-route(?=\s)', Keyword, 'slurp'),
            (r'ssh(?=\s)', Keyword, 'ssh'),
            (r'subnet-zero(?=\s)', Keyword, 'slurp'),
            (r'summary-address(?=\s)', Keyword, 'slurp'),
            (r'tacacs(?=\s)', Keyword, 'slurp'),
            (r'tcp(?=\s)', Keyword, 'slurp'),
            (r'telnet(?=\s)', Keyword, 'slurp'),
            (r'tftp(?=\s)', Keyword, 'slurp'),
            (r'trigger-authentication(?=\s)', Keyword, 'slurp'),
            (r'udptn(?=\s)', Keyword, 'slurp'),
            (r'unnumbered(?=\s)', Keyword, 'slurp'),
            (r'unreachables(?=\s)', Keyword, 'slurp'),
            (r'urd(?=\s)', Keyword, 'slurp'),
            (r'verify(?=\s)', Keyword, 'slurp'),
            (r'vrf(?=\s)', Keyword, 'slurp'),
            (r'wccp(?=\s)', Keyword, 'slurp'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'ip access-group options': [
            (r'\s', Text),
            include('litInteger'),
            include('litString'),
            (r'in|out', Keyword, '#pop'),
            ],

        'ip-address': [
            (r'$', Text, '#pop'),
            (r'\s(?=[0-9.]+\s)', Text, ('ip-address options', 'litNetmask', 'litAddress')),
            (r'\s(?=\S+/)', Text, ('ip-address options', 'litPrefixLen', 'litAddress')),
            (r'\s', Text),
            ],
            
        'acl': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'dynamic-extended(?=\s)', Keyword, 'slurp'),
            (r'rate-limit(?=\s)', Keyword, 'slurp'),
            (r'\d+', Number.Integer, 'slurp'),
            (r'\S+', String, 'slurp'),
            ],

        'ip-address options': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'secondary(?=\s)', Keyword.Pseudo),
            ],

        'ip-route': [
            (r'$', Text, '#pop'),
            (r'\s(?=[0-9.]+\s)', Text, ('ip route options', 'ip route dest', 'litNetmask', 'litAddress')),
            (r'\s(?=\S+/)', Text, ('ip route options', 'ip route dest', 'litPrefixLen', 'litAddress')),
            (r'profile', Keyword, 'slurp'),
            (r'\s', Text),
            ],

        'ip route dest': [
            include('litAddress'),
            include('litInterfaceName'),
            ],

        'ip route options': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            include('litInteger'),
            (r'name(?=\s)', Keyword, 'litString'),
            (r'permanent(?=\s)', Keyword),
            (r'tag(?=\s)', Keyword, 'litInteger'),
            (r'track(?=\s)', Keyword, 'litInteger'),
            ],

        'http': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'server(?=\s)', Keyword, 'slurp'),
            (r'secure-server(?=\s)', Keyword, 'slurp'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],
            
        'ntp': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'clock-period(?=\s)', Keyword, 'slurp'),
            (r'server(?=\s)', Keyword, 'litAddress'),
            (r'source(?=\s)', Keyword, 'slurp'),
            (r'update-calendar(?=\s)', Keyword, 'slurp'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'scp': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'server(?=\s)', Keyword, 'litKeyword'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'ssh': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'version(?=\s)', Keyword, 'litInteger'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'line': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'access-class(?=\s)', Keyword, 'slurp'),
            (r'accounting(?=\s)', Keyword, 'slurp'),
            (r'authorization(?=\s)', Keyword, 'slurp'),
            (r'autocomamnd(?=\s)', Keyword, 'slurp'),
            (r'autocommand-options(?=\s)', Keyword, 'slurp'),
            (r'data-character-bits(?=\s)', Keyword, 'slurp'),
            (r'databits(?=\s)', Keyword, 'slurp'),
            (r'domain-lookup(?=\s)', Keyword, 'slurp'),
            (r'editing(?=\s)', Keyword, 'slurp'),
            (r'escape-character(?=\s)', Keyword, 'slurp'),
            (r'exec(?=\s)', Keyword, 'slurp'),
            (r'exec-banner(?=\s)', Keyword, 'slurp'),
            (r'exec-character-bits(?=\s)', Keyword, 'slurp'),
            (r'exec-timeout(?=\s)', Keyword, 'slurp'),
            (r'flowcontrol(?=\s)', Keyword, 'slurp'),
            (r'full-help(?=\s)', Keyword, 'slurp'),
            (r'history(?=\s)', Keyword, 'slurp'),
            (r'international(?=\s)', Keyword, 'slurp'),
            (r'ipv6(?=\s)', Keyword, 'slurp'),
            (r'length(?=\s)', Keyword, 'slurp'),
            (r'location(?=\s)', Keyword, 'slurp'),
            (r'logging(?=\s)', Keyword, 'slurp'),
            (r'login(?=\s)', Keyword, 'slurp'),
            (r'modem(?=\s)', Keyword, 'slurp'),
            (r'monitor(?=\s)', Keyword, 'slurp'),
            (r'motd-banner(?=\s)', Keyword, 'slurp'),
            (r'no(?=\s)', Operator.Word),
            (r'notify(?=\s)', Keyword, 'slurp'),
            (r'padding(?=\s)', Keyword, 'slurp'),
            (r'parity(?=\s)', Keyword, 'slurp'),
            (r'password(?=\s)', Keyword, 'slurp'),
            (r'privilege(?=\s)', Keyword, 'slurp'),
            (r'refuse-message(?=\s)', Keyword, 'slurp'),
            (r'rotary(?=\s)', Keyword, 'slurp'),
            (r'rxspeed(?=\s)', Keyword, 'slurp'),
            (r'session-timeout(?=\s)', Keyword, 'slurp'),
            (r'special-character-bits(?=\s)', Keyword, 'slurp'),
            (r'speed(?=\s)', Keyword, 'slurp'),
            (r'start-character(?=\s)', Keyword, 'slurp'),
            (r'stop-character(?=\s)', Keyword, 'slurp'),
            (r'stopbits(?=\s)', Keyword, 'slurp'),
            (r'terminal-type(?=\s)', Keyword, 'slurp'),
            (r'timeout(?=\s)', Keyword, 'slurp'),
            (r'transport(?=\s)', Keyword, 'slurp'),
            (r'txspeed(?=\s)', Keyword, 'slurp'),
            (r'vacant-message(?=\s)', Keyword, 'slurp'),
            (r'width(?=\s)', Keyword, 'slurp'),
            ],

        'logging': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'buffered(?=\s)', Keyword, 'slurp'),
            (r'buginf(?=\s)', Keyword, '#pop'),
            (r'cns-events(?=\s)', Keyword, 'slurp'),
            (r'console(?=\s)', Keyword, 'slurp'),
            (r'count(?=\s)', Keyword, '#pop'),
            (r'exception(?=\s)', Keyword, 'slurp'),
            (r'facility(?=\s)', Keyword, 'slurp'),
            (r'filter(?=\s)', Keyword, 'slurp'),
            (r'history(?=\s)', Keyword, 'slurp'),
            (r'host(?=\s)', Keyword, 'litHost'),
            (r'monitor(?=\s)', Keyword, 'slurp'),
            (r'on(?=\s)', Keyword, '#pop'),
            (r'origin-id(?=\s)', Keyword, 'slurp'),
            (r'queue-limit(?=\s)', Keyword, 'slurp'),
            (r'rate-limit(?=\s)', Keyword, 'slurp'),
            (r'reload(?=\s)', Keyword, 'slurp'),
            (r'server-arp(?=\s)', Keyword, '#pop'),
            (r'source-interface(?=\s)', Keyword, 'slurp'),
            (r'trap(?=\s)', Keyword, 'slurp'),
            (r'userinfo(?=\s)', Keyword, '#pop'),
            include('litHost'),
            (r'\S+', Keyword.Pseudo, '#pop'),
            ],

        'radius': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'host(?=\s)', Keyword, ('slurp', 'litHost')),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'router': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'!.*', Comment),
            (r'bgp(?=\s)', Keyword, ('bgp', 'litInteger')),
            (r'isis(?=\s)', Keyword, ('isis', 'litInteger')),
            (r'ospf(?=\s)', Keyword, ('ospf', 'litInteger')),
            (r'no(?=\s)', Operator.Word),
            ],

        'bgp': [
            (r'^(?=\S)', Text, '#pop'),
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'!.*', Comment),
            (r'address-family(?=\s)', Keyword, 'slurp'),
            (r'aggregate-address(?=\s)', Keyword, 'slurp'),
            (r'auto-summary(?=\s)', Keyword, 'slurp'),
            (r'bgp(?=\s)', Keyword, 'slurp'),
            (r'capability(?=\s)', Keyword, 'slurp'),
            (r'compatible(?=\s)', Keyword, 'slurp'),
            (r'default-information(?=\s)', Keyword, 'slurp'),
            (r'default-metric(?=\s)', Keyword, 'slurp'),
            (r'distance(?=\s)', Keyword, 'slurp'),
            (r'distribute-list(?=\s)', Keyword, 'slurp'),
            (r'exit-address-family(?=\s)', Keyword, 'slurp'),
            (r'exit-peer-policy(?=\s)', Keyword, 'slurp'),
            (r'exit-peer-session(?=\s)', Keyword, 'slurp'),
            (r'export(?=\s)', Keyword, 'slurp'),
            (r'ha-mode(?=\s)', Keyword, 'slurp'),
            (r'import(?=\s)', Keyword, 'slurp'),
            (r'inherit(?=\s)', Keyword, 'slurp'),
            (r'ip(?=\s)', Keyword, 'slurp'),
            (r'match(?=\s)', Keyword, 'slurp'),
            (r'maximum paths(?=\s)', Keyword, 'slurp'),
            (r'neighbor(?=\s)', Keyword, ('bgp neighbor', 'litAddress')),
            (r'network(?=\s)', Keyword, 'slurp'),
            (r'no(?=\s)', Operator.Word),
            (r'redistribute(?=\s)', Keyword, 'slurp'),
            (r'router(?=\s)', Keyword, 'slurp'),
            (r'scope(?=\s)', Keyword, 'slurp'),
            (r'synchronization(?=\s)', Keyword, 'slurp'),
            (r'table-map(?=\s)', Keyword, 'slurp'),
            (r'template(?=\s)', Keyword, 'slurp'),
            (r'timers(?=\s)', Keyword, 'slurp'),
            ],

        'bgp neighbor': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'activate(?=\s)', Keyword, 'slurp'),
            (r'distribute-list(?=\s)', Keyword, 'slurp'),
            (r'ebgp-multihop(?=\s)', Keyword, 'slurp'),
            (r'next-hop-self(?=\s)', Keyword, 'slurp'),
            (r'password(?=\s)', Keyword, 'slurp'),
            (r'remote-as(?=\s)', Keyword, ('slurp', 'litInteger')),
            (r'remove-private-as(?=\s)', Keyword, 'slurp'),
            (r'route-map(?=\s)', Keyword, 'slurp'),
            (r'send-community(?=\s)', Keyword, 'slurp'),
            (r'soft-reconfiguration(?=\s)', Keyword, 'slurp'),
            (r'update-source(?=\s)', Keyword, 'slurp'),
            (r'version(?=\s)', Keyword, 'slurp'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],
                
        'ospf': [
            (r'^(?=\S)', Text, '#pop'),
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'!.*', Comment),
            (r'area(?=\s)', Keyword, 'slurp'),
            (r'auto-cost(?=\s)', Keyword, 'slurp'),
            (r'capability(?=\s)', Keyword, 'slurp'),
            (r'compatible(?=\s)', Keyword, 'slurp'),
            (r'default(?=\s)', Keyword, 'slurp'),
            (r'default-information(?=\s)', Keyword, 'slurp'),
            (r'default-metric(?=\s)', Keyword, 'slurp'),
            (r'discard-route(?=\s)', Keyword, 'slurp'),
            (r'distance(?=\s)', Keyword, 'slurp'),
            (r'distribute-list(?=\s)', Keyword, 'slurp'),
            (r'domain-id(?=\s)', Keyword, 'slurp'),
            (r'domain-tag(?=\s)', Keyword, 'slurp'),
            (r'ignore(?=\s)', Keyword, 'slurp'),
            (r'ispf(?=\s)', Keyword, 'slurp'),
            (r'limit(?=\s)', Keyword, 'slurp'),
            (r'log-adjacency-changes', Keyword),
            (r'max-lsa(?=\s)', Keyword, 'slurp'),
            (r'max-metric(?=\s)', Keyword, 'slurp'),
            (r'maximum paths(?=\s)', Keyword, 'slurp'),
            (r'neighbor(?=\s)', Keyword, 'slurp'),
            (r'network(?=\s)', Keyword, ('ospf-area', 'litNetmask', 'litAddress')),
            (r'no(?=\s)', Operator.Word),
            (r'passive-interface(?=\s)', Keyword, 'slurp'),
            (r'queue-depth(?=\s)', Keyword, 'slurp'),
            (r'redistribute(?=\s)', Keyword, 'slurp'),
            (r'router-id(?=\s)', Keyword, 'litAddress'),
            (r'summary-address(?=\s)', Keyword, 'slurp'),
            (r'timers(?=\s)', Keyword, 'slurp'),
            (r'traffic-share(?=\s)', Keyword, 'slurp'),
            ],

        'isis': [
            (r'^(?=\S)', Text, '#pop'),
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'!.*', Comment),
            (r'address-family(?=\s)', Keyword, 'slurp'),
            (r'adjacency-check(?=\s)', Keyword, 'slurp'),
            (r'advertise(?=\s)', Keyword, 'slurp'),
            (r'area-password(?=\s)', Keyword, 'slurp'),
            (r'authentication(?=\s)', Keyword, 'slurp'),
            (r'default(?=\s)', Keyword, 'slurp'),
            (r'default-information(?=\s)', Keyword, 'slurp'),
            (r'distance(?=\s)', Keyword, 'slurp'),
            (r'domain-password(?=\s)', Keyword, 'slurp'),
            (r'fast-flood(?=\s)', Keyword, 'slurp'),
            (r'hello(?=\s)', Keyword, 'slurp'),
            (r'ignore-lsp-errors(?=\s)', Keyword, 'slurp'),
            (r'ip(?=\s)', Keyword, 'slurp'),
            (r'is-type(?=\s)', Keyword, 'slurp'),
            (r'ispf(?=\s)', Keyword, 'slurp'),
            (r'log-adjacency-changes', Keyword),
            (r'lsp-full(?=\s)', Keyword, 'slurp'),
            (r'lsp-gen-interval(?=\s)', Keyword, 'slurp'),
            (r'lsp-mtu(?=\s)', Keyword, 'slurp'),
            (r'lsp-refresh-interval(?=\s)', Keyword, 'slurp'),
            (r'max-area-addresses(?=\s)', Keyword, 'slurp'),
            (r'max-lsp-lifetime(?=\s)', Keyword, 'slurp'),
            (r'maxium-paths(?=\s)', Keyword, 'slurp'),
            (r'metric(?=\s)', Keyword, 'slurp'),
            (r'metric-style(?=\s)', Keyword, 'slurp'),
            (r'net(?=\s)', Keyword, 'slurp'),
            (r'no(?=\s)', Operator.Word),
            (r'partition(?=\s)', Keyword, 'slurp'),
            (r'passive-interface(?=\s)', Keyword, 'slurp'),
            (r'prc-interval(?=\s)', Keyword, 'slurp'),
            (r'protocol(?=\s)', Keyword, 'slurp'),
            (r'redistribute(?=\s)', Keyword, 'slurp'),
            (r'set-attached-bit(?=\s)', Keyword, 'slurp'),
            (r'set-overload-bit(?=\s)', Keyword, 'slurp'),
            (r'spf-interval(?=\s)', Keyword, 'slurp'),
            (r'summary-address(?=\s)', Keyword, 'slurp'),
            (r'traffic-share(?=\s)', Keyword, 'slurp'),
            (r'update-queue-depth(?=\s)', Keyword, 'slurp'),
            (r'use(?=\s)', Keyword, 'slurp'),
            ],

        'ospf-area': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'area(?=\s)', Keyword, 'ospfAreaLiteral'),
            ],

        'snmp-server': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'chassid-id(?=\s)', Keyword, 'slurp'),
            (r'community(?=\s)', Keyword, ('slurp', 'snmp-server community options')),
            (r'contact(?=\s)', Keyword, 'slurp'),
            (r'drop(?=\s)', Keyword, 'slurp'),
            (r'enable(?=\s)', Keyword, 'slurp'),
            (r'engineID(?=\s)', Keyword, 'slurp'),
            (r'group(?=\s)', Keyword, 'slurp'),
            (r'host(?=\s)', Keyword, 'slurp'),
            (r'ifindex(?=\s)', Keyword, 'slurp'),
            (r'inform(?=\s)', Keyword, 'slurp'),
            (r'location(?=\s)', Keyword, 'slurp'),
            (r'manager(?=\s)', Keyword, 'slurp'),
            (r'packetsize(?=\s)', Keyword, 'slurp'),
            (r'queue-length(?=\s)', Keyword, 'slurp'),
            (r'system-shutdown(?=\s)', Keyword, 'slurp'),
            (r'tftp-server-list(?=\s)', Keyword, 'slurp'),
            (r'trap(?=\s)', Keyword, 'slurp'),
            (r'trap-source(?=\s)', Keyword, 'slurp'),
            (r'trap-timeout(?=\s)', Keyword, 'slurp'),
            (r'user(?=\s)', Keyword, 'slurp'),
            (r'view(?=\s)', Keyword, 'slurp'),
            (r'\S+', Keyword.Pseudo, 'slurp'),
            ],

        'snmp-server community options': [
            include('litString'),
            ],

        'username': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'\S+', String, 'slurp'),
            ],

        'vlan': [
            (r'$', Text, '#pop'),
            (r'\s', Text),
            (r'internal(?=\s)', Keyword, 'slurp'),
            (r'\d+', Number.Integer, ('#pop', 'vlan int')),
            ],

        'vlan int': [
            (r'^\s+', Whitespace),
            (r'\s', Text),
            (r'^(?=\S)', Text, '#pop'),
            (r'name(?=\s)', Keyword, 'litString'),
            ],
            
        'slurp': [
            (r'.*$', Text, '#pop'),
            ],

        'litInteger': [
            (r'\s', Text),
            (r'\d+', Number.Integer, '#pop'),
            ],

        'litBareWord': [
            (r'\s', Text),
            (r'\S+', String, '#pop'),
            ],

        'litString': [
            (r'\s', Text),
            (r'(")(.*?)(\1)', bygroups(Punctuation, String.Double, Punctuation), '#pop'),
            (r'\S+', String, '#pop'),
            ],

        'litStringEOL': [
            (r'\s', Text),
            (r'.*$', String, '#pop'),
            ],

        'litKeyword': [
            (r'\s', Text),
            (r'\S+', Keyword, '#pop'),
            ],

        'litHeredoc': [
            (r'\s', Text),
            (r'(?s)(\S)(.*?)(\1)', bygroups(Punctuation, String.Heredoc, Punctuation), '#pop'),
            ],

        'litInterfaceName': [
            (r'\s', Text),
            (r'\S+\s\d{1,2}(/\d+)?', Name.Variable, '#pop'),
            (r'\S+', Name.Variable, '#pop'),
            ],

        'litHost': [
            include('litAddress'),
            include('litString'),
            ],

        'litAddress': [
            (r'\s', Text),
            include('litV4Address'),
            include('litV6Address'),
            ],
        
        'litV4Address': [
            (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', Number.Integer, '#pop'),
            ],
        
        'litV6Address': [
            (r'(([\dA-Fa-f]{1,4}\:{1,2})|\:{2,2})([\dA-Fa-f]{1,4}\:{1,2}){0,6}[\dA-Fa-f]{0,4}', Number.Hex, '#pop'),
            ],

        'litNetmask': [
            (r'\s', Text),
            include('litV4Address'),
            ],
           
        'litPrefixLen': [
            (r'\s', Text),
            (r'(/)(\d{1,3})', bygroups(Punctuation, Number.Integer), '#pop'),
            ],

        'ospfAreaLiteral': [
            (r'\s', Text),
            (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', Number.Integer, '#pop'),
            (r'\d+', Number.Integer, '#pop'),
            ],

        'access-list': [
            (r'\n', Text, '#pop'),
            (r'\s+', Text),
            (r'(permit|deny|ip|any|log|host|icmp|tcp)\b', Keyword),
            ],

        }