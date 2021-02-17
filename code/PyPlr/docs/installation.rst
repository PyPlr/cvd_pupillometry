Installation
============

:mod:`PyPlr` and its dependencies are easy to install. For Mac OS X or Linux, simply run: 

.. code-block:: bash

    $ git clone https://github.com/PyPlr
    $ cd PyPlr
    $ pip install -r requirements.txt
    $ python setup.py install

:mod:`PyPlr` is also registered on `PyPI <https://pypi.org/>`_ and the latest release can be installed with `pip` (this will also install the dependencies automatically):

.. code-block:: bash

    $ pip install pyplr

(`link to the PyPI project page <https://pypi.org/project/pyplr/>`_).

The latest development version can also be installed from GitHub with `pip`

.. code-block:: bash

    $ pip install git+https://github.com/spitschan/PyPlr.git


Requirements
------------

:mod:`PyPlr` requires Python3 and a range of standard numerical computing packages (all of which listed in the file `requirements.txt`)

.. include:: ../requirements.txt
   :literal:

The following additional packages may also be helpful:

.. include:: ../dev-requirements.txt
   :literal:

All requirements can be installed by running :code:`pip install -r requirements.txt`.

Virtual environments
--------------------

We recommend installing :mod:`PyPlr` in a virtual environment. This can be done using either `Python's virtual environments <https://docs.python.org/3/tutorial/venv.html>`_ or `conda <https://docs.conda.io/en/latest/>`_. 

.. code-block:: bash

    $ conda create -n pyplr python=3.7.7
    $ conda activate pyplr
    $ conda install --file requirements.txt

The :mod:`spectres` package may need to be installed using `pip`

.. code-block:: bash

    $ pip install spectres

Notes/Potential Issues
-------------------------

Various... put them all here
