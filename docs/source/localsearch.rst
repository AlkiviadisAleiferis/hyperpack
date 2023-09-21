Local search
============

Solving with local_search
-------------------------

Do a hill-climbing, 2-opt exchange local search with the default potential points strategy (see `theory <https://github.com/AlkiviadisAleiferis/hyperpack-theory/blob/main/a_hyper_heuristic_for_solving_variants_of_the_2D_binpacking_problem.pdf>`_).
A brief explanation of the local search procedure :ref:`here<local_search>`.

.. code-block:: python

    >>> from hyperpack import HyperPack
    >>> problem_data = {
    >>>     "containers": containers,
    >>>     "items": items,
    >>>     "settings": settings
    >>> }
    >>> problem = HyperPack(**problem_data)
    >>> problem.local_search()

After solving has finished, the best solution can be found in :ref:`problem.solution<solution_structure>` instance attribute.

Potential points strategy
-------------------------

If you want to override the potential points strategy used, simply set the proper value to the ``potential_points_strategy``
attribute.

The attribute is managed and protected by deletion and assignment validation:
    - It must be a tuple (immutability).

    - It must contain only proper potential points (see ``HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY`` for reference).

    - It cannot be deleted.

    - Must not contain duplicate points.

In every invalid case, a ``PotentialPointsError`` will be raised with approriate message and logging.
