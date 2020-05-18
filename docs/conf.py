# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../'))

# -- Project information -----------------------------------------------------

project = 'queenbee'
copyright = '2020, Ladybug Tools'
author = 'Ladybug Tools'

# The short X.Y version
version = ''

# The full version, including alpha/beta/rc tags
release = ''


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
	'sphinxcontrib.fulltoc',
	'sphinx.ext.napoleon',
    'sphinx_click.ext',
    'm2r',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

html_extra_path = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
import sphinx_bootstrap_theme

# html_theme = 'alabaster'
html_theme = 'bootstrap'
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    # For black navbar, do "navbar navbar-inverse"
    'navbar_class': "navbar navbar-inverse",
    # Fix navigation bar to top of page?
    # Values: "true" (default) or "false"
    'navbar_fixed_top': "true",
	'navbar_pagenav': True,
    'source_link_position': "nav",
	'bootswatch_theme': "united",
    'bootstrap_version': "3",
    'globaltoc_depth': 3,
	}

# on_rtd is whether we are on readthedocs.org
# on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# if not on_rtd:  # only import and set the theme if we're building docs locally
#    import sphinx_rtd_theme
#    html_theme = 'sphinx_rtd_theme'
#    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'css/jsv.css',
    'css/app.css',
]

html_js_files = [
    'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.5/ace.js',
    'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.5/mode-json.js',
    'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.5/theme-chrome.js',
    'https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.15.0/lodash.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/tv4/1.2.7/tv4.min.js',
    'js/ref-parser.min.js',
    'js/jsv.js',
    'js/app.js',
]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
html_sidebars = {
    # '**': ['localtoc.html']
   '**': ['localtoc.html'],
}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'ladybugdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'ladybug.tex', 'ladybug Documentation',
     'Ladybug Tools', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'ladybug', 'ladybug Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'ladybug', 'ladybug Documentation',
     author, 'ladybug', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

import json

from queenbee._openapi import get_openapi
from queenbee.operator import Operator
from queenbee.recipe import Recipe
from queenbee.workflow import Workflow


with open('_static/schemas/workflow-openapi.json', 'w') as out_file:
    json.dump(
        get_openapi(schema_class=Workflow, title='Queenbee Workflow Schema', description='Schema documentation for Queenbee Workflows'),
        out_file,
        indent=2
    )

with open('_static/schemas/operator-openapi.json', 'w') as out_file:
    json.dump(
        get_openapi(schema_class=Operator, title='Queenbee Operator Schema', description='Schema documentation for Queenbee Operators'),
        out_file,
        indent=2
    )

with open('_static/schemas/recipe-openapi.json', 'w') as out_file:
    json.dump(
        get_openapi(schema_class=Recipe, title='Queenbee Recipe Schema', description='Schema documentation for Queenbee Recipes'),
        out_file,
        indent=2
    )
    json.dump(get_openapi(schema_class=Recipe), out_file, indent=2)


with open('_static/schemas/workflow-schema.json', 'w') as out_file:
    out_file.write(Workflow.schema_json())

with open('_static/schemas/operator-schema.json', 'w') as out_file:
    out_file.write(Operator.schema_json())

with open('_static/schemas/recipe-schema.json', 'w') as out_file:
    out_file.write(Recipe.schema_json())