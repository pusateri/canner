Using a Custom Canner with netCannery
-------------------------------------

netCannery can be configured to use a custom Canner instead of the one
bundled with the application.  To use a custom canner:

1. Open netCannery.

2. From the :guilabel:`netCannery` menu, select
   :guilabel:`Preferences...`.
   
3. Click on the :guilabel:`Advanced` tab.

4. Check :guilabel:`Use Custom Canner` and enter the full path to your
   custom canner.

.. note::

   During operation, ``canner`` spawns taggers as child processes.
   Other than adding the variables defined in the :ref:`tagger API
   <tagger-api>`, ``canner`` does not modify the environment before
   spawning taggers.  This can cause unexpected results if Canner is not
   installed in standard system locations.

   The convention is to create a ``canner-wrapper`` script that sets up
   the environment correctly and then calls ``canner``.  (The virtual
   environment script above automatically does this for you.)  Be sure
   to specify the path to ``canner-wrapper`` in the netCannery
   preferences dialog.

