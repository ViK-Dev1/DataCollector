# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DataCollector'
copyright = '2026, H.Vikram'
author = 'H.Vikram'
release = 'v1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = ['myst_parser']
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
html_css_files = ["custom1.css"]
html_theme_options = {
    "top_of_page_buttons": [],  # empty list = no buttons
    "light_logo": "botLogo.png",
    "dark_logo": "botLogo.png"
}

'''
Put this CSS in furo.css after the build command

a:link, a:visited {
  color: #7bed9f !important;
}
7bed9f - day
05c46b - dark
'''
