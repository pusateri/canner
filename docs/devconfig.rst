.. highlight:: none

Device Configuration Hints
==========================

HP Procurve
-----------

The HP Procurve switches are much easier to communicate with if you
turn off the formatting for VT100::

   hostname# configure
   hostname(config)# console terminal none


Extreme Networks Extremeware
----------------------------

Older versions of Extremeware store the console paging state *in* the
configuration::

   disable clipaging

If you set this while talking to the box interactively, it will modify
the configuration, so we recommend you set it and save it in the
configuration.

.. vim: ft=rst sts=3 sw=3 tw=72:
