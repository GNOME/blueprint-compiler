""" Contains all the syntax beyond basic objects, properties, signal, and
templates. """

from .gobject_object import Object
from .gobject_property import Property
from .gobject_signal import Signal
from .gtk_a11y import A11y
from .gtk_combo_box_text import Items
from .gtk_file_filter import mime_types, patterns, suffixes
from .gtk_layout import Layout
from .gtk_menu import menu
from .gtk_size_group import Widgets
from .gtk_string_list import Strings
from .gtk_styles import Styles
from .gtkbuilder_child import Child
from .gtkbuilder_template import Template
from .ui import UI
from .values import IdentValue, TranslatedStringValue, FlagsValue, LiteralValue

from .common import *

OBJECT_HOOKS.children = [
    menu,
    Object,
]

OBJECT_CONTENT_HOOKS.children = [
    Signal,
    Property,
    A11y,
    Styles,
    Layout,
    mime_types,
    patterns,
    suffixes,
    Widgets,
    Items,
    Strings,
    Child,
]

VALUE_HOOKS.children = [
    TranslatedStringValue,
    FlagsValue,
    IdentValue,
    LiteralValue,
]
