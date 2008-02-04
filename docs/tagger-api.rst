:Version: $Id$

Tagger Filter API Version 1.0
=============================

Overview
--------
This document explains the Application Programmer Interface (API) for each Tagger invoked by the open source *Canner* project. A *Tagger* is program script that expects to execute in a particular environment and will create *tags* that describe properties of a network device.

Tag Components
--------------

  Tag Name
    The name of the tag being created
    
  Tag Sort Name
    An alternate form of the tag name used for sorting. Needed for numerical sorting or for IP addresses.
    
  Tag Display Name
    An alternate form of the tag name for display to the user.
    
  Tag Kind
    A classification of the tag for comparing similar tags.
    
  Context Tag Name
    The name of a qualifier tag so other instances of the created tag can be differentiated. A tag can be created multiple times in different contexts.
    
  Context Tag Kind
    A classification of the context tag.

Environment Variables
---------------------

  SESSION_DEVICE
    The device contacted
    
  SESSION_ID
    A unique session ID for the snapshot
    
  SESSION_OS_NAME
    The personality of the device
    
  SESSION_TIMESTAMP
    The time the snapshot was taken
    
  SESSION_USER
    The user login name under which to execute commands on the device

  TRIGGER_NAME
    The tag that triggered this tagger to be executed.
    
  TRIGGER_SORT_NAME
    The trigger tag represented in a format for sorting
    
  TRIGGER_DISPLAY_NAME
    The trigger tag represented in a format for display
    
  TRIGGER_KIND
    A classification of the tag to allow for grouping
    
  TRIGGER_CONTEXT_NAME
    A qualifier Tag for the trigger Tag to differentiate multiple references to the same tag
    
  TRIGGER_CONTEXT_KIND
    A classification of the trigger context Tag for grouping
    
  TRIGGER_FILENAME
    The filename that triggered the tagger to be executed. The tagger may parse this file to generate tags.
    
  TRIGGER_LINE
    The line number in the file triggering the tagger to be executed. If the tagger is executed as a result of the file being created, the line number won't be set.
    
  TRIGGER_TAGGER
    The tagger that is being executed.

Arguments
---------

  There are currently no command line arguments passed to the tagger.


Output File Format
------------------

  The output of a tagger are individual tags formatted in JavaScript Object Notation (`JSON`_, `RFC 4627`_). Each tag is required to have the following properties: name, kind, and filename. Optional properties include sortName, displayName, line, and context (which itself is a Tag).
  
  Here are two example output tags from a tagger::

    [
        {
           "tag": {
             "kind": "IPv4 subnet",
             "name": "24.1.2.0\/28",
             "sortName": "18010200\/28"
           },
           "context": {
             "kind": "IPv4 address",
             "name": "24.1.2.3",
             "sortName": "18010203"
           },
           "filename": "foo.txt"
        },
        {
           "tag": {
             "kind": "IPv4 interface",
             "name": "24.1.2.3",
             "sortName": "18010203"
           },
           "filename": "foo.txt"
        }
    ]

Notice that a context tag can refer to a Tag that has not necessarily been created yet.

.. _JSON: http://www.json.org/
.. _RFC 4627: http://www.ietf.org/rfc/rfc4627.txt

Directory Structure
-------------------
  Commands
  
  Executable programs

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