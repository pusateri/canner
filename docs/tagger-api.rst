:Version: $Id$

Tagger Filter API Version 1.0
=============================

Overview
--------
  This document explains the Application Programmer Interface (API) for each Tagger invoked by the open source *Canner* project. A *Tagger* is program script that expects to execute in a particular environment and will create *tags* that describe properties of a network device.

Tags
----

  A Tag is represented by a name and qualified with a kind. Tags of the same kind are comparable. A double-dash is used to separate a tag's kind from its name. An example would be 'name server--ns.foo.com' where "name server" is the kind and ns.foo.com is the name.

  A Tag can also have an optional 'sort name' and 'display name'. Without these, the name is used for sorting and display.

  Tags can imply other tags creating ancestor/descendant relationships. This is accomplished through the use of the 'implies' or 'implied by' tag references. As an example, 'ospf area--0.0.0.0' is a tag that implies 'routing-protocol--ospf' and tag 'IPv4 subnet--10.1.1.0/24' is 'implied by' tag 'IPv4 address--10.1.1.1' (and the knowledge of the prefix length on the interface).

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

  There are currently no command line arguments passed to the tagger.


Output File Format
------------------

  The output of a tagger are individual tags formatted in JavaScript Object Notation (`JSON`_, `RFC 4627`_). The tag has a name qualified by a kind. The optional location is a filename optionally followed by a line number separated by a colon (:).
  
  Here are two example output tags from a tagger::

    [
        {
           "location": "foo.txt:100",
           "tag": "IPv4 subnet--24.1.2.0/28",
           "sort name": "18010200/28",
           "implied by": "IPv4 address--24.1.2.3"
         
        },
        {
           "location": "foo.txt:100",
           "tag": "IPv4 address--24.1.2.3",
           "sort name": "18010203"
        }
    ]
    

  The first time a tag is used, it springs into existence. Use of 'implies' or 'implied by' is mutually exclusive. A "sort name" and "display name" can also be associated with a tag. These traits of a tag will replace existing traits from previous usages.

.. _JSON: http://www.json.org/
.. _RFC 4627: http://www.ietf.org/rfc/rfc4627.txt

Directory Structure
-------------------
  Taggers are organized in a directory structure which implies their dependency on other taggers. The names of the directories are either a tag 'kind' or a qualified tag containing 'kind--name'.
  
  Initially, the personality of a device is determined using a 'show version' command from the tagger engine. The top level tagger directory has a sub-directory for each known operating system (OS) as well as other potential qualified tag names or kinds.
  
  In order to execute a command on a device, a new tag sub-directory is created of kind 'file' followed by the double dash (--) and the name of the file to save the output of the command to. The actual command to run on the device is placed inside the directory using a filename 'Command'. As an example, the sub-directory file--running.cfg would contain a file called 'Command' containing the line 'show running-config'. Also in that sub-directory would be any taggers that should be executed to parse the output of the command.

  As the taggers are run and tags are used, the tagger scripts for those tags are also run. This allows a dependency chain to be created so that the appropriate taggers are run for the appropriate devices.


Well known Tag Kinds
--------------------
  address family 
  
  admin status

  autonomous system

  BGP group

  BGP peer

  BOOTP relay

  chassis

  config log

  config user

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

  OPSFv3 area

  OS

  OSPF area

  OSPFv2 area

  physical interface

  physical interface

  RADIUS server

  registered network

  registered network subnet

  registered organization

  routing protocol

  service

  snapshot date

  snapshot device

  snapshot ID

  snapshot month

  snapshot timestamp

  snapshot user

  snapshot year

  user

  version

  VLAN ID

More Information
----------------

#. For more information about the *Canner* open source project, please visit the `Canner Website`_. Mailing lists, bug reports, and tagger submissions can all be handled at this site.

.. _Canner Website: http://canner.bangj.com