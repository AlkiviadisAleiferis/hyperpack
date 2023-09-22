Hypersearch
============

Solving with hyper_search
-------------------------

This method implements a potentially :ref:`exhaustive<hyper_search>` search for maximum bin utilization.

.. code-block:: python

    >>> from hyperpack import HyperPack
    >>> problem_data = {
    >>>     "containers": containers,
    >>>     "items": items,
    >>>     "settings": settings
    >>> }
    >>> problem = HyperPack(**problem_data)
    >>> problem.hypersearch(
    >>>     orientation="wide",
    >>>     sorting_by=("area", True)
    >>> )

.. note::

    ``orientation`` parameter is used for :ref:`orient_items<orient_items>` method.

    ``sorting_by`` parameter is used for :ref:`sort_items<sort_items>` method.

Presorting and orientation can impact the solution's speed and quality. Pass ``None`` to
these parameters to skip these operations.

After solving has finished, the solution can be found in :ref:`problem.solution<solution_structure>` instance attribute.

What this method generally does is **it deploys a local search for every potential points strategy sequence available**.
That means all the possible permutations of the potential points.

For more on potential points see the `theory <https://github.com/AlkiviadisAleiferis/hyperpack-theory/blob/main/a_hyper_heuristic_for_solving_variants_of_the_2D_binpacking_problem.pdf>`_
or :ref:`here<Potential points concept>`

In case multiprocessing is used, the pool of strategies is divided to chuncks, and distributed to the generated
subprocesses. Every subprocess executes a local search for every strategy in the chunck, and is coordinated
with the rest of the processes through a mutually accessed ``multiprocessing.Array`` object.

If a maximum utilization is found (i.e. all the bins have 100% utilization), the processes are informed through the ``Array``,
and the execution stops.

Upon exiting the winning process delivers the "goods", that is the process with the best found solution.

Generally the stopping criteria of the hypersearch are:
    1. Maximum utilization found.
    2. Max time in seconds has been surpassed.
    3. An error occured in runtime.

.. note::

    When using ``hypersearch``, ``throttle=False`` argument passing can be used to make totally thorough
    search on big instances of the problem (>71) items, pussing the local search to check all neighbors
    of every node. Beware that this process is really time consuming.
