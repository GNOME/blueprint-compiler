""" Contains all the syntax beyond basic objects, properties, signal, and
templates. """

from .gtk_a11y import a11y
from .gtk_file_filter import mime_types, patterns, suffixes
from .gtk_layout import layout
from .gtk_menu import menu
from .gtk_size_group import widgets
from .gtk_styles import styles

OBJECT_HOOKS = [menu]

OBJECT_CONTENT_HOOKS = [a11y, styles, layout, mime_types, patterns, suffixes, widgets]
