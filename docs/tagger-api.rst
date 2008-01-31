:Version: $Id$

Tagger Filter API Version 1.0
=============================

Overview
========
This document explains the Application Programmer Interface (API) for the Tagger Filters (or taggers) invoked by the open source *Canner* project. A *Tagger* is program filter that expects to execute in particular environment and will create *tags* that describe properties of a network device.

Environment Variables
=====================

TAG_
SESSION_

SESSION_DEVICE
SESSION_ID
SESSION_OS
SESSION_TIMESTAMP
SESSION_USER

TAG
TAG_CONTEXT
TAG_FILENAME
TAG_LINE
TAG_SORT_NAME
TAG_TAGGER

Arguments
=========

Tag Components
==============

#. Tag name
#. Tag kind
#. Context tag name
#. Context tag kind
#. sort name
#. display name

Output File Format
==================

Directory Structure
===================
Command
Executable Filters

Well known tags and their formats
=================================

Examples
========

Troubleshooting
===============

More Information
================

#. For more information about the *Canner* open source project, please visit the `Canner Website`_. Mailing lists, bug reports, and tagger submissions can all be handled at this site.

#. The official YAML syntax can be found in the `YAML Documentation`_

.. _Canner Website: http://canner.bangj.com
.. _YAML Documentation: http://www.yaml.org