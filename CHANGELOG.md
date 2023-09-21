# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/) (<major>.<minor>.<patch>).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the Deprecations section of releases.


## [1.0.1] - 2023-09-21

### Bug fixes

Fixed issue where using create_figure while omitting "figure"
key in settings, if plotly version was < 5.14.0 or missing, plotly would have raised error.

### Improved docs

Changed settings parameter depiction.

Improved docstrings

## [1.0.0] - 2023-09-20

Initial version published.
