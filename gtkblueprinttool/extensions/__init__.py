""" Contains all the syntax beyond basic objects, properties, signal, and
templates. """

from .gtk_a11y import a11y
from .gtk_menu import menu
from .gtk_styles import styles
from .gtk_layout import layout

OBJECT_HOOKS = [menu]

OBJECT_CONTENT_HOOKS = [a11y, styles, layout]
