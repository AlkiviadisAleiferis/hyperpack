import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.getcwd()).parent.parent))
import hyperpack
from hyperpack import heuristics

sys.modules["heuristics"] = heuristics

project = "hyperpack"
copyright = "2023, Alkiviadis Aleiferis"
author = hyperpack.__author__
release = hyperpack.__version__

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx_rtd_dark_mode",
]

templates_path = ["_templates"]
exclude_patterns = []

# user starts in light mode
default_dark_mode = False
html_theme = "sphinx_rtd_theme"
html_logo = "./_static/hyperpack_logo.png"
html_static_path = ["_static"]
# html_theme_options = {
#     'analytics_anonymize_ip': False,
#     'logo_only': False,
#     'display_version': True,
#     'prev_next_buttons_location': 'bottom',
#     'style_external_links': False,
#     'vcs_pageview_mode': '',
#     'style_nav_header_background': 'white',
#     # Toc options
#     'collapse_navigation': True,
#     'sticky_navigation': True,
#     'navigation_depth': 4,
#     'includehidden': True,
#     'titles_only': False
# }
