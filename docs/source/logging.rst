Logging
========

Two loggers are used inside the library. The ``"pointgenpack"`` logger and the ``"hyperpack"``.

The former one is used for debugging the Point Generation hueristic, and is solely used for development.

The latter one is used throughout the library and is user intended on INFO level (DEBUG level is used mostly for development).

Use the logger like this:

.. code-block:: python

   import logging
   logger = logging.getLogger("hyperpack")

.. note::

   When library's exceptions are raised, the logger logs the message of the Exception with ERROR level.
