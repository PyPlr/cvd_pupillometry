Installation
============

*PyPlr* is registered on `PyPI <https://pypi.org/>`_, which means the latest version can be installed easily via the *pip* packaging tool (this will also install the dependencies automatically):

.. code-block:: bash

    $ pip install pyplr

(`link to the PyPI project page <https://pypi.org/project/pyplr/>`_).

The latest development version can also be installed from GitHub with *pip*:

.. code-block:: bash

    $ pip install git+https://github.com/PyPlr/cvd_pupillometry.git

Alternatively, you can clone from from git and install with `setuptools <https://setuptools.readthedocs.io/en/latest/index.html>`_:

.. code-block:: bash

    $ git clone https://github.com/PyPlr/cvd_pupillometry.git PyPlr
    $ cd PyPlr
    $ python setup.py install

If you want to make changes to the code and have those changes instantly available on `sys.path` you can use setuptools' `develop mode <https://setuptools.readthedocs.io/en/latest/userguide/development_mode.html>`_:

.. code-block:: bash

    $ python setup.py develop

Requirements
------------

*PyPlr* requires Python3 and a set of standard numerical computing packages, all of which are listed in *requirements.txt*:

.. include:: ../requirements.txt
   :literal:

The following additional packages may also be helpful for development:

.. include:: ../dev-requirements.txt
   :literal:

All requirements can be installed by running :code:`pip install -r requirements.txt`.

Virtual environments
--------------------

We recommend installing *PyPlr* in a virtual environment. This can be done using either `Python's virtual environments <https://docs.python.org/3/tutorial/venv.html>`_ or `conda <https://docs.conda.io/en/latest/>`_:

.. code-block:: bash

    $ conda create -n pyplr python=3.7.7
    $ conda activate pyplr
    $ python setup.py install

Notes/Potential Issues
----------------------

We are aware of the following:

* psychopy thread issue - revert to pyglet=1.4.10

.. rubric:: Tables and indices
------------------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
