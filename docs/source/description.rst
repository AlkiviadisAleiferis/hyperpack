Description
===========

.. image:: ./_static/hyperpack_logo.png
   :align: center
   :height: 100
   :alt: hyperpack

Problem description
-------------------

The hyperpack library is an API for solving instances of the `2D Binpacking problem`_.
Many different variations can be created and solved, accordind to the instantiation data.

The theory of this library's implementation can be found in author's
document `"A hyper-heuristic for solving variants of the 2D bin packing problem" <https://github.com/AlkiviadisAleiferis/hyperpack-theory/blob/main/a_hyper_heuristic_for_solving_variants_of_the_2D_binpacking_problem.pdf>`_.

.. _`2D Binpacking problem`: https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=2cb8247534c9e889ac42b2362f0ad96c8c6b8c77

Please feel free to open any issues for future development, try benchmarks of the library, or provide innovating ideas.

The variants can be summarized in the below characteristics:
  - Any number and sizes of (rectangular) items (small objects)
  - Any number and sizes of (rectangular) bins (large objects)
  - The items can be rotated or not.

Currently the library solves only packing problems, but a customization may be made in
the future for strip packing problems also.

Also a possible new version could be the pre-solving formulation of the bin to accomplish
more complex shapes than a simple rectangular bin.

The bin packing problem has been used in many sectors of the industry, and mostly where manufacturing or
industrial management needs arise.

Potential points concept
-------------------------

Two very important concepts will be passed around in this library, called **potential points** and **potential points strategy**.

Potential points:
  They are the points of the container (bin) that an item can be placed. On placement the origin point
  of the item (bottom left corner) is placed on that point.

  These points are divided to specific classes, which in runtime are pools of points to be selected
  for item placement.

  The total potential points classes are these: ``(A, B, C, D, A', B', A", B", E, F)``

  Each item when placed in the bin spawns new potential points. The points generated are a function of

    1. the placement position
    2. the existing items in the container.

Potential points strategy:
  Is the sequence by which a `potential points class pool` is picked for drawing a potential point for
  placing the next item.

  For example if the porential points strategy is ``(A, B, C, D, A', B', A", B", E, F)``, then in each item placement
  first a class A pool of potential points will be choesen for picking a placement point.
  If that class is empty then a class B pool and so on.

The **A.** potential points strategy and the **B.** items sequence provided to the Point Generation construction heuristic, together
create deterministic solutions. **That is if the same items sequence is given and the same strategy, the output will be the same**.

PointGenPack class
------------------

This class focuses in solving using the construction heuristic developed (can
be found in `theory <https://github.com/AlkiviadisAleiferis/hyperpack-theory/blob/main/a_hyper_heuristic_for_solving_variants_of_the_2D_binpacking_problem.pdf>`_ ) with an input of a:

  - sequence of objects
  - set of containers
  - potential points strategy (see theory)

It is a lower level class, that implements the construction heuristic solution along with
other functionalities as:

  - creating/showing the figure(s) of the solution (``create_figure`` method).
  - custom deepcopy methods for class attributes for better speed.
  - attribute management (``items``, ``containers``, ``settings``).
  - validation of the given problem's ``settings``.


HyperPack class
-----------------

This class implements the higher level metaheuristic/hyper-heuristic search, utilizing
the lower level class PointGenPack. There are two functionalities for optimizing instances
of the problem:

.. _local_search:

Local search (local_search method)
######################################

An implementation of the 2-opt hill-climbing local search procedure, changing each time the
input :ref:`items<items>` sequence passed to the construction heuristic.

  - Starts from the ``self.items`` sequence, and doing continuous 2-opt exchanges feeds the new sequence to the PointGen's solve method.
  - A new optimum signals that a new **node** is found. The operation starts again from that node, until another node is found.
  - If no new node is found the local search terminates, and sets the best found values to the current values of the :ref:`solution<solution structure>`.

.. _hyper_search:

Hyper-heuristic search (hypersearch method)
###############################################

This method implements the hyper-heuristic search, aiming at total parsing of the :ref:`potential points strategies<Potential points concept>`.
Uses a local search for every strategy, alterating the constructive heuristic in each iteration.


The operation is multiprocessing enabled, in which case the total strategies are distributed to all the available
workers (processor threads), for faster solving speed.
