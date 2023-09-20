Figures
========

Figures guide
-------------

.. _figures_guide:

.. warning::

  - every figure related operation requires `plotly`_ (version >= 5.14.0)
  - exportation to image (not html) requires `kaleido`_ (version >= 0.2.1).

  If "figure" key has been given in settings with proper structure, or the ``create_figure`` method is called
  and the plotly requirement isn't met in the execution environment, a ``SettingsError`` will be raised.

  If "figure" key has been given in settings with proper structure, with exportation to type image
  and the kaleido requirement isn't met in the execution environment, a ``SettingsError`` will be raised.

.. _`plotly`: https://plotly.com/python/
.. _`kaleido`: https://pypi.org/project/kaleido/

The decision was made for minizing the library's dependencies and also for providing the freedom
of the user to implement his own figures utilizing the :ref:`problem.solution<solution_structure>` attribute which
is available after solving.

Here is an example of a figure with plotly. ``"i_0"``, ``"i_1"``, ... are the items' ids.

.. raw:: html
    :file: ./_static/example_graph.html

All the settings for the figure are provided in the ``"figure"`` key of the :ref:`settings<settings_param>` parameter.

Omit ``"figure"`` key for no figure export operations. You can still see the figure thought by calling ``problem.create_figure(show=True)``
after a solution has been found.

If the ``"figure"`` key is given, validation on figure settings will take place with appropriate errors.

If the ``"export"`` key exists in the ``"figure"`` nested dictionary, exportation will take place accordingly to ``"export"`` settings' values.

All the figure settings can be seen :ref:`here<settings_param>`

.. note::

    If a solution hasn't been found yet, a ``Can't create figure if a solution hasn't been found`` warning message will be logged,
    when ``create_figure`` is called.

.. note::

  All figure operations are done with the ``create_figure`` method.

----------------------------

Show figure
-----------

After solving has finished, calling

.. code-block:: python

  >>> problem.create_figure()

will open the figure in the system's default browser in html format, if ``settings`` -> ``figure`` -> ``{"show" : True}``.

If the settings ``"show"`` key isn't given, the below method call will do the trick.

.. code-block:: python

  >>> problem.create_figure(show=True)

The settings ``"show"`` value has precedence over the ``create_figure``'s ``show`` parameter.

----------------------------

Export figure
-------------

If the ``"figure"`` key in settings is has an ``"export"`` key,
according to this key's value a corresponfing exportation will take place.

In case anything goes wrong during the exportation process, a ``FigureExportError`` will be raised.

plotly library is required for figure creation, and kaleido for exportation to **image type only**, as mentioned above.

figure's file name
##################

Each container will have it's corresponding figure.

Each figure's file name will be determined by the ``"file_name"`` key.

  - The file's output name(s) will have the format

    .. code-block:: python

        f"{file_name}__{container_id}.{format}"

  - The file's name(s) must be complying with the following regex:

    .. code-block:: python

        r"^[a-zA-Z0-9_-]{1,45}$"

  - If ``"file_name"`` key is omitted, the ``"file_name"`` value will default to ``"PlotlyGraph"``.

figure's export path
####################

Determined by the ``"path"`` key. A ``SettingsError`` wil be raised if:

  - ``"path"`` isn't a valid, existing, absolute path of a directory (folder).
  - ``"path"`` is omitted or isn't of type ``str``.

exporting to html
#################

Determined by the ``"type"`` key value -> ``"html"``.

  - Enable exporation providing ``"html"`` value on ``"type"`` key.
  - Omitting the ``"format"`` key won't raise a ``SettingsError``, as the ``".html"`` format is fixed.
  - ``"width"`` or ``"length"`` keys' values won't affect the process in any way, but will cause ``SettingsError`` if given with invalid values.

exporting to image (pdf, png, jpeg, webp, svg)
##############################################

Determined by the ``"type"`` key value -> ``"image"``.

  - If the ``"type"`` key's value is ``"image"``, an image will be exported to the provided path.
  - Image exportation depends on **kaleido** package. If not present in environment, a ``SettingsError`` will be raised.
  - Omitting ``"format"`` will raise a ``SettingsError``.
  - ``"format"`` can have any of the values (``"pdf"``, ``"png"``, ``"jpeg"``, ``"webp"``, ``"svg"``).
  - ``"width"`` and ``"height"`` can be omitted, and a default 1700x1700px size will be given. If given, they must be positive integers, or a ``SettingsError`` will be raised.
  - If **kaleido** (version >= 0.2.1) isn't found in execution environment, a ``SettingsError`` will be raised.

figure's export format
######################

It's the file extension and is determined by the ``"format"`` key.

    **If exportation is done to** ``html`` type, format is unecessary to be provided, and if it is provided
    it won't affect the operation or validation, since the format is standard ``.html`` extension.
    Also the kaleido library is not required.

    **If exportation is done to** ``"image"`` type, the format must be given and be compatible with the choices
    mentioned in the settings parameter structure, or a ``SettingsError`` wil be raised. Also the **kaleido** library
    must be installed.

Example
-------

.. code-block:: python

    containers = {"container-id": {"W": 4, "L": 4}}
    items = {
        "i-0": {"w": 1, "l": 1},
        "i-1": {"w": 2, "l": 1},
        "i-2": {"w": 1, "l": 1},
        "i-3": {"w": 4, "l": 2},
        "i-4": {"w": 2, "l": 2},
    }
    settings = {
        "figure": {
            "export": {
                "type": "html",
                "file_name": "example",
                "path": "C:\\Users\\alkiv\\Desktop\\",
            }
        }
    }
    p = HyperPack(items=items, containers=containers, settings=settings)
    p.local_search()
    p.create_figure(show=True)

.. raw:: html
    :file: ./_static/example__container-id.html

The exported file will have a file name ``example__container-id.html``.

Overriding create_figure
------------------------

The ``create_figure`` method can be overridden, and a custom figure implementation can be made with another package, using
the :ref:`solution structure<solution_structure>` attribute, as well as the ``containers`` and ``items`` attributes.
