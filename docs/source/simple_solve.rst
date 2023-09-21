Solve
======

Solves for all the containers. Implements the `point generation construction
heuristic <https://github.com/AlkiviadisAleiferis/hyperpack-theory/blob/main/a_hyper_heuristic_for_solving_variants_of_the_2D_binpacking_problem.pdf>`_.

.. code-block:: python

    >>> from hyperpack import HyperPack
    >>> problem_data = {
    >>>     "containers": containers,
    >>>     "items": items,
    >>>     "settings": settings
    >>> }
    >>> problem = HyperPack(**problem_data)
    >>> problem.solve()


- Populates ``self.solution`` with solution found for every container.
- Populates ``self.obj_val_per_container`` with the utilization of every container.

An extensive description can be found in :ref:`reference <reference_point_gen_pack>`

This method cannot produce quality solutions. It is utilized by ``local_search`` and ``hyper_search``
in higher level operations.
