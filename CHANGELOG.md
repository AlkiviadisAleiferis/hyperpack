# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) (<major>.<minor>.<patch>).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the Deprecations section of releases.

---------------------------

# [1.1.0] - 2023-09-21


### Strip Packing

Now the HyperPack class can solve strip packing instances of certain width.
See the docs for extended guide.

### Changes

- Improved running time by around 20% by:

    - Implementing 'collections.deque' for potential points pools.
    - Implementing arrays for container's coordinate system.

- Error in multiprocessing hypersearch now logs the traceback to 'hyperpack' logger.
- More robustness through extended testing.
- Updated figures. Now the figures have titles on top left and x, y axis titles.
- Local Search has been abstracted and the code has been organized accordingly.

### Improved docs

- Improved doctrings and documentation.

### Bug fixes
- Fixed where running multiprocessing hypersearch, the settings "workers_num" changed to 1

---------------------------

# [1.0.1] - 2023-09-21

### Bug fixes

- Fixed issue where using create_figure while omitting "figure" key in settings, if plotly version was < 5.14.0 or missing, plotly would have raised error.

### Improved docs

- Changed settings parameter depiction.

- Improved docstrings

---------------------------

## [1.0.0] - 2023-09-20

Initial version published.
