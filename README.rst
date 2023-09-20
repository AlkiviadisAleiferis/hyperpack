.. image:: https://github.com/AlkiviadisAleiferis/hyperpack/blob/main/docs/source/_static/hyperpack_logo.png?raw=true
   :align: center
   :width: 40%
   :alt: hyperpack

-----------------------------

.. image:: https://img.shields.io/badge/License-Apache_2.0-blue.svg

.. image:: https://img.shields.io/badge/python-3.7|3.8|3.9|3.10|3.11-blue.svg

.. image:: https://img.shields.io/badge/maintainer-alkiviadis.aliferis@gmail.com-blue.svg

.. image:: https://img.shields.io/badge/pypi-v1.0.0-blue.svg

Problem description
-------------------

The hyperpack library is an API for solving instances of the `2D Binpacking problem`_.
Many different variations can be created and solved, accordind to the instantiation data.

The theory of this library's implementation can be found in author's
document `"A hyper-heuristic for solving variants of the 2D bin packing problem"`_.

.. _`"A hyper-heuristic for solving variants of the 2D bin packing problem"`: https://github.com/AlkiviadisAleiferis/hyperpack-theory

.. _`2D Binpacking problem`: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=2cb8247534c9e889ac42b2362f0ad96c8c6b8c77

The solvable variants can be summarized in the below characteristics:
  - Any number and sizes of (rectangular) items (small objects)
  - Any number and sizes of (rectangular) bins (large objects)
  - The items can be rotated or not.

Currently the library solves only packing problems, but a customization may be made also in
the future for strip packing problems.

The bin packing problem has been used in many sectors of the industry, and mostly where manufacturing or
industrial management needs arise.

Installation
-------------

Install using pip:

    ``pip install hyperpack``

Defining the problem
---------------------

Instantiate your problem with proper arguments

.. code-block:: python

    >>> from hyperpack import HyperPack
    >>> problem = hyperpack.HyperPack(
    >>>     containers=containers, # problem parameter
    >>>     items=items, # problem parameter
    >>>     settings=settings # solver/figure parameters
    >>> )

According to the arguments given, the corresponding problem will be instantiated, ready to be solved
with provided guidelines. The items and containers (bins) structure:

.. code-block:: python

    containers = {
        "container-0-id": {
            "W": int, # > 0 container's width
            "L": int # > 0 container's length
        },
        "container-1-id": {
            "W": int, # > 0 container's width
            "L": int # > 0 container's length
        },
        # ... rest of the containers
        # minimum 1 container must be provided
    }

    items = {
        "item_0_id": {
            "w": int, # > 0 item's width
            "l": int, # > 0 item's length
        },
        "item_1_id": {
            "w": int, # > 0 item's width
            "l": int, # > 0 item's length
        },
        # ... rest of the items
        # minimum 1 item must be provided
    }

See documentation for detailed settings structure.

Usage
-----

Do Local search with default settings:

.. code-block:: python

    >>> from hyperpack import HyperPack
    >>> problem = HyperPack(**problem_data)
    >>> problem.local_search()

After solving has finished, the solution can be found in ``problem.solution`` instance attribute.

Alternatively for a deep search and maximum bin utilization in mind:

.. code-block:: python

    >>> problem = HyperPack(**problem_data)
    >>> problem.hypersearch()

Solution logging
-----------------

Use the ``log_solution`` method to log an already found solution:

.. code-block:: python

    >>> problem.log_solution()
    SOLUTION LOG:
    Percent total items stored : 100.0000%
    Container: container_0 60x30
            [util%] : 100.0000%
    Container: container_1 60x50
            [util%] : 91.2000%

    Remaining items : []

Create a figure
-----------------

**Warning** : plotly (5.14.0 or greater) is needed for figure creation and kaleido (0.2.1 or greater)
for figure exportation to image. These libraries are not listed as dependencies providing liberty
of figure implementation.

.. code-block:: python

  >>> problem.create_figure(show=True)

The figure below is opened in default browser:

.. image:: https://github.com/AlkiviadisAleiferis/hyperpack/blob/main/docs/source/_static/README_figure.png?raw=true
   :align: center
   :width: 100%
   :alt: example_figure

For more information, visit the documentation page.

Future development
-------------------

Many ideas and concepts can be implemented in this library. The most propable depending on
the community's interest:

    - Augmentation of the objective function to deal with a bigger plethora of problems.
    - Implementation of the strip packing problem.
    - Django integrations.
    - Large Neighborhood Search for big instances of the problem.
    - Other shapes of the container.
    - A dynamic live terminal display.
    - Execution speed optimization.
    - Multiprocessing for the local search alone (combined with LNS).
    - More detailed figures.
    - Figures with other libraries (matplotlib).

If interested with development with some of these features please contact me.

Theoretical foundations
-----------------------

This packages inner mechanics and theoretical design are based upon this `documentation`_.

.. _`documentation`: https://github.com/AlkiviadisAleiferis/hyperpack-theory

Donations
----------

Donations are much appreciated and compensate for the workhours invested in creating this package.
If you 're using hyperpack commercially and get monetary value from it's functionalities, please
consider a donation of any size. These donations can help maintain and extend the operability of this library.

You can use this `link`_  for donating.

.. _`link`: https://www.paypal.com/donate/?hosted_button_id=QESY46KQV94V2
