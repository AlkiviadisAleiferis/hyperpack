Strip packing
=============

As of v1.1 the library supports solving strip packing instances (no guillotine cuts).

If you want to solve a strip packing problem, simply instantiate ``HyperPack`` with
a ``strip_pack_width`` integer argument, instead of ``containers`` argument.

**Beware** that providing a containers argument would raise a ContainersError.

**Also trying to change the containers attribute in any way in strip packing**
**instances, raises an error.**

Now the problem instance is **--exclusively--** a strip packing problem.

.. code-block:: python

    >>> prob = HyperPack(items=items, strip_pack_width=10)
    >>> # a strip packing width problem is ready to be solved

Now calling ``hypersearch`` or ``local_search``
will do the following:

- Will try to pack all the items to the smallest possible height.
- Every new better solution will push the `imaginary container's height` to the height
  of the new better accepted solution.
- Every solution that **doesn't include all the items given will not be accepted**.

The above restriction of the container height according to 100% items inclusion can be overridden
throught the ``container_min_height`` attribute:

.. code-block:: python

    >>> prob.container_min_height = 10 # int > 0

Now solving will bypass the total items inclusion restriction and pushes the
imaginary container to smaller heights if a better solution is found,
**with a minimum height restriction of 10**.

Reducing the container's height forces packing to better solutions due to the
Point Generations mechanics and the nature of the local search.

.. note::

  The imaginary container's height is the height of the strip used for packing.

Concluding, if a better utilization of the strip is wanted for trade of number of items
included in packing, push strip packing to smaller heights
utilizing the ``container_min_height`` attribute.

.. warning::

  After solving, the container's height and ``container_min_height`` remains the same
  from previous solutions, **with the exception of multiprocessing hypersearch**.

  If you want to reset the strip's height to initial and
  ``container_min_height`` to ``None``, call ``reset_container_height``:

  .. code-block:: python

    >>> prob = HyperPack(**problem_data)
    >>> prob.settings["workers_num"] == 1
    True
    >>> prob.container_height
    200
    >>> prob.container_min_height = 100
    >>> prob.hypersearch()
    >>> prob.container_height < 200
    True
    >>> prob.reset_container_height()
    >>> prob.container_height
    200
    >>> prob.container_min_height == None
    True
    >>>
    >>> # now with multiprocessing ------
    >>>
    >>> prob = HyperPack(**problem_data_mp)
    >>> prob.settings["workers_num"] > 1
    True
    >>> prob.container_height
    200
    >>> prob.hypersearch()
    >>> prob.container_height == 200
    True

  Of course another way would be explicit assignment to ``container_height``
  and ``container_min_height`` attributes.


Apart from the above differentiations, the figures, logging,
containers and items structure, remain the same.
