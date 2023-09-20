Benchmarks/Example
==================

A set of benchmark datasets can be found in ``hyperpack.benchmark.datasets.hopper_and_turton_2000``

.. code-block:: python

    >>> import hyperpack
    >>> # C1, C2, C3, C4, C5, C6, C7
    >>> C3 = hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3
    >>> containers = C3.containers
    >>> items = C3.items_a # or items_b or items_c
    >>> problem = hyperpack.HyperPack(containers=containers, items=items)
    >>> print(len(items_a)) # number of items
    28
    >>> print(problem.containers)
    Containers
    - id: container_0
        width: 60
        length: 30
    >>> problem.local_search()

In development mode (clone repository locally), a commands.py argument parsing custom command module
has some available tools for profiling and automatically creating graphs for certain tests

.. code-block:: python

    >>> python3 -m commands
    Development tool for various operations.

    arguments:
        --create-tests-graphs:
            Creates all the potential points tests graphs automatically
            by inspecting the pytests parametrize parameters for every test.

        --profile:
            Profile the local search for the corresponding benchmarks.
            Available choices:
                C1, C2, ..., C7

        -p , --problem: the specific items set for profiling. Defaults to 'a'.
            Available choices:
                a, b, c
