# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) (<major>.<minor>.<patch>).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the Deprecations section of releases.

---------------------------

# [1.2.0] - 2023-12-26

### Changes
Inner structure changes have been implemented for maximum scalability and maintainability.
Thus for framework purposes the library gets a new MINOR semantic version.

Changes implemented:
- Added ``generate_problem_data`` function for quickstarting purposes in hyperpack.utils.
- Implemented refactoring with mixins/abstractions for better SOLID compliance and maintainability.
- Many inner workings refactors for better readability and functionality.
- Removed info logs at start/end of hypersearch.
- ``AbstractStructure`` renamed to ``AbstractStructureSet``. Refactor is backward compatible since it is not exposed to client funcitonality.

### Changes (dev)

New command for version checking.


### Improved docs

- Improved doctrings and documentation.

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
