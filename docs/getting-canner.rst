.. highlight:: sh

Getting Canner
==============

Canner comes bundled as part of the netCannery_ application.  If you are
interested in trying out Canner and are running Mac OS X Leopard,
netCannery provides an easy to use and install option.  If you are
interested in running Canner standalone or in making your own changes to
Canner, you will need to checkout and install a copy.

Canner is maintained using the Mercurial_ source control management
system. It is similar to Subversion or CVS but provides an easier way
for different organizations to make local modifications and still merge
changes from the project.

.. _netCannery: http://bangj.com/netcannery
.. _Mercurial: http://www.selenic.com/mercurial


Requirements
------------

* Python 2.5
* Perl
* C compiler (Xcode or other GCC)


Installing
----------

The main engine in Canner is written in Python and the project is
packaged and installed as a Python egg.  It can be installed as a normal
Python package or using a virtual environment (recommended).

Traditional Installation
........................

1. Install Mercurial.

   Installable packages are available from `the Mercurial website`_.

.. _`the Mercurial website`: http://www.selenic.com/mercurial/wiki/index.cgi/BinaryPackages

2. Clone Canner from the Mercurial repository::

   $ hg clone http://canner.bangj.com/hg/canner
   
3. Run the setup script::

   $ cd canner
   $ python setup.py install

Virtual Environment Installation
................................

Canner can also be installed as a self-contained virtual Python
environment courtesy of virtualenv_.  The virtual environment allows you
to install and run Canner without modifying your standard Python
installation.

.. _virtualenv: http://pypi.python.org/pypi/virtualenv

To install Canner using a virtual environment, 

1. Download the canner-boot.py_ script.

.. _canner-boot.py: http://canner.bangj.com/hg/canner/raw-file/tip/setup.py

2. Run the script and specify a directory for the virtual environment::

   $ python canner-boot.py mycannerenv

Before developing in the virtual environment, it must be activated::

   $ source mycannerenv/bin/activate

Activating the environment sets your shell to use the virtualenv instead
of your system's Python.  If you open up a new shell, you will need to
run ``activate`` in it before you can work on Canner in it.

If you simply want to run Canner out of your virtual environment, use
the supplied ``canner-wrapper`` script.  It will set up the environment
and then call the real ``canner`` script::

   $ mycannerenv/bin/canner-wrapper -v -u fred device.example.com

.. vim: ft=rst sts=3 sw=3 tw=72:
