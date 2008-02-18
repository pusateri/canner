:Version: $Id$

Tagger Filter API Version 1.0
=============================

Overview
--------
This document explains the Application Programmer Interface (API) for each Tagger invoked by the open source *Canner* project. A *Tagger* is an executable that expects to run in a particular environment and will create *tags* that describe properties of a network device. Taggers can be written in any language. The executables can be compiled code or scripts that are run through an interpreter or command shell. The taggers write the tags to standard output (stdout). Standard input (stdin) is closed.

Tags
----
A Tag is represented by a name and qualified with a kind. Tags of the same kind are comparable. A double-dash is used to separate a tag's kind from its name. An example would be 'name server--ns.foo.com' where "name server" is the kind and ns.foo.com is the name.

A Tag can also have an optional 'sort_name' and 'display_name'. Without these, the name is used for sorting and display.

Tags can imply other tags creating ancestor/descendant relationships. This is accomplished through the use of the 'implies' or 'implied_by' tag references. As an example, 'OSPF area--0.0.0.0' is a tag that implies 'routing-protocol--OSPF' and tag 'IPv4 subnet--10.1.1.0/24' is 'implied_by' tag 'IPv4 address--10.1.1.1'. References to other Tags can be resolved by other taggers.

Environment Variables
---------------------

The following environment variables are passed to the tagger for its use during execution:
  
  SESSION_DEVICE
    The device contacted
    
  SESSION_ID
    A unique session ID for the snapshot
    
  TRIGGER_KIND
    A classification of the tag to allow for grouping

  TRIGGER_NAME
    The tag that triggered this tagger to be executed.
                  
  TRIGGER_FILENAME
    The filename that triggered the tagger to be executed. The tagger may parse this file to generate tags.
        
Arguments
---------

Since the taggers rely on the above environment variables, there are currently no command line arguments passed to the tagger.


Output Format
-------------
The output of a tagger are individual tags formatted in JavaScript Object Notation (`JSON`_, `RFC 4627`_). 

The tag has a name qualified by a kind. The optional location is a filename optionally followed by a line number separated by a colon (:). The first time a tag is used, it springs into existence. Either 'implies' or 'implied_by' can be used independently or both can be used in the same tag usage for different relationships. A "sort_name" and "display_name" can also be associated with a tag. These traits of a tag will replace existing traits from previous usages.
  
Here are two example output tags from a tagger::

    [
        {
           "location": "foo.txt:100",
           "tag": "IPv4 subnet--24.1.2.0/28",
           "sort_name": "18010200/28",
           "display_name": "24.1.2/28",
        },
        {
           "location": "foo.txt:100",
           "tag": "IPv4 address--24.1.2.3",
           "sort_name": "18010203"
           "implies": "IPv4 subnet--24.1.2.0/28"
        }
    ]


.. _JSON: http://www.json.org/
.. _RFC 4627: http://www.ietf.org/rfc/rfc4627.txt

Tagger Dependencies
-------------------
Taggers are organized in a directory structure which implies their dependency on other taggers. The names of the directories are either a tag 'kind' or a qualified tag containing 'kind--name'.

As directories are descended by matching tags, new taggers are discovered and added to a known list. Taggers are executed when a matching tag or tag kind is found. As new tags are created, matching taggers are executed and new directories are discovered. This causes new taggers to be run for existing tags and the process continues. A dependency chain is created ensuring the appropriate taggers are run for the appropriate devices.

Initially, the personality of a device is determined using a 'show version' command from the tagger engine. The top level tagger directory has a sub-directory for each known operating system (OS) as well as other potential qualified tag names or kinds.
  
In order to execute a command on a device, a new tag sub-directory is created of kind 'file' followed by the double dash (--) and the name of the file to save the output of the command to. The actual command to run on the device is placed inside the directory using a filename 'Command'. As an example, the sub-directory file--running.cfg would contain a file called 'Command' containing the line 'show running-config'. Also in that sub-directory would be any taggers that should be executed to parse the output of the command.


Well known Tag Kinds
--------------------
A non-exhaustive list of tag kinds can be found below. This list will constantly be growing as new taggers are written, submitted to the project, and merged from other sources. New kinds can be defined at any time by any one but unnecessary duplication is discouraged to maximize comparisons since only tags of like kinds can be compared.

  address family 
  
  admin status

  autonomous system

  BGP group

  BGP peer

  BOOTP relay

  chassis

  config log

  config user

  device

  domain name

  file

  flag

  hostname

  interface

  interface description

  interface type

  IPv4 address

  IPv4 subnet

  IPv6 address

  IPv6 subnet

  module

  MSDP group

  MSDP peer

  name server

  NTP server

  OS

  OSPF area

  OSPFv2 area

  OSPFv3 area
  
  physical interface

  physical interface

  RADIUS server

  registered network

  registered network subnet

  registered organization

  routing protocol

  service

  snapshot

  snapshot date

  snapshot month

  snapshot timestamp

  snapshot user

  snapshot year

  user

  version

  VLAN ID

More Information
----------------

For more information about the *Canner* open source project, please visit the `Canner Website`_. Mailing lists, bug reports, and tagger submissions can all be handled at this site.

.. _Canner Website: http://canner.bangj.com