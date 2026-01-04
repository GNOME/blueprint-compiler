===========
Diagnostics
===========


.. _Diagnostic abstract_class:

abstract_class
--------------
Objects can't be created from abstract classes. Abstract classes are used as base classes for other classes, but they don't have functionality on their own. You may want to use a non-abstract subclass instead.


.. _Diagnostic bad_syntax:

bad_syntax
----------
The tokenizer encountered an unexpected sequence of characters that aren't part of any known blueprint syntax.


.. _Diagnostic child_not_accepted:

child_not_accepted
------------------
The parent class does not have child objects (it does not implement `Gtk.Buildable <https://docs.gtk.org/gtk4/iface.Buildable.html>`_ and is not a subclass of `Gio.ListStore <https://docs.gtk.org/gio/class.ListStore.html>`_). Some classes use properties instead of children to add widgets. Check the parent class's documentation.


.. _Diagnostic conversion_error:

conversion_error
----------------
The value's type cannot be converted to the target type.

Subclasses may be converted to their superclasses, but not vice versa. A type that implements an interface can be converted to that interface's type. Many boxed types can be parsed from strings in a type-specific way.


.. _Diagnostic expected_bool:

expected_bool
-------------
A boolean value was expected, but the value is not ``true`` or ``false``.


.. _Diagnostic extension_not_repeatable:

extension_not_repeatable
------------------------
This extension can't be used more than once in an object.


.. _Diagnostic extension_wrong_parent_type:

extension_wrong_parent_type
---------------------------
No extension with the given name exists for this object's class (or, for a :ref:`child extension<Syntax ChildExtension>`, the parent class).


.. _Diagnostic invalid_number_literal:

invalid_number_literal
----------------------
The tokenizer encountered what it thought was a number, but it couldn't parse it as a number.


.. _Diagnostic member_dne:

member_dne
----------
The value is being interpreted as a member of an enum or flag type, but that type doesn't have a member with the given name.


.. _Diagnostic missing_gtk_declaration:

missing_gtk_declaration
-----------------------
All blueprint files must start with a GTK declaration, e.g. ``using Gtk 4.0;``.


.. _Diagnostic multiple_templates:

multiple_templates
------------------
Only one :ref:`template<Syntax Template>` is allowed per blueprint file, but there are multiple. The template keyword indicates which object is the one being instantiated.


.. _Diagnostic namespace_not_found:

namespace_not_found
--------------------
The ``.typelib`` files for the given namespace could not be found. There are several possibilities:

* There is a typo in the namespace name, e.g. ``Adwaita`` instead of ``Adw``

* The version number is incorrect, e.g. ``Adw 1.0`` instead of ``Adw 1``. The library's documentation will tell you the correct version number to use.

* The packages for the library are not installed. On some distributions, the ``.typelib`` file is in a separate package from the main library, such as a ``-devel`` package.

* There is an issue with the path to the typelib file. The ``GI_TYPELIB_PATH`` environment variable can be used to add additional paths to search.


.. _Diagnostic namespace_not_imported:

namespace_not_imported
----------------------
The given namespace was not imported at the top of the file. Importing the namespace is necessary because it tells blueprint-compiler which version of the library to use.


.. _Diagnostic object_dne:

object_dne
----------
No object with the given ID exists in the current scope.


.. _Diagnostic property_dne:

property_dne
------------
The class or interface doesn't have a property with the given name.


.. _Diagnostic property_convert_error:

property_convert_error
----------------------
The value given for the property can't be converted to the property's type.


.. _Diagnostic property_construct_only:

property_construct_only
-----------------------
The property can't be bound because it is a construct-only property, meaning it can only be set once when the object is first constructed. Binding it to an expression could cause its value to change later.


.. _Diagnostic property_read_only:

property_read_only
------------------
This property can't be set because it is marked as read-only.


.. _Diagnostic signal_dne:

signal_dne
----------
The class or interface doesn't have a signal with the given name.


.. _Diagnostic type_dne:

type_dne
--------
The given type doesn't exist in the namespace.


.. _Diagnostic type_not_a_class:

type_not_a_class
----------------
The given type exists in the namespace, but it isn't a class. An object's type must be a concrete (not abstract) class, not an interface or boxed type.


.. _Diagnostic version_conflict:

version_conflict
----------------
This error occurs when two versions of a namespace are imported (possibly transitively) in the same file. For example, this will cause a version conflict:

.. code-block:: blueprint

   using Gtk 4.0;
   using Gtk 3.0;

But so will this:

.. code-block:: blueprint

   using Gtk 4.0;
   using Handy 1;

because libhandy imports ``Gtk 3.0``.


.. _Diagnostic wrong_compiler_version:

wrong_compiler_version
----------------------
This version of blueprint-compiler is for GTK 4 blueprints only. Future GTK versions will use different versions of blueprint-compiler.


Linter Rules
------------

.. _Diagnostic adjustment_prop_order:

adjustment_prop_order
~~~~~~~~~~~~~~~~~~~~~
An `Adjustment <https://docs.gtk.org/gtk4/class.Adjustment.html>`_'s ``value`` property must be set after the ``lower`` and ``upper`` properties. Otherwise, it will be clamped to 0 when it is set, since that is the default lower and upper bounds of the Adjustment.


.. _Diagnostic avoid_all_caps:

avoid_all_caps
~~~~~~~~~~~~~~
According to the `GNOME Human Interface Guidelines <https://developer.gnome.org/hig/guidelines/typography.html>`_, labels should not use all capital letters.


.. _Diagnostic gtk_switch_state:

gtk_switch_state
~~~~~~~~~~~~~~~~
The `state <https://docs.gtk.org/gtk4/property.Switch.state.html>`_ property controls the backend state of the switch directly. In most cases, you want to use `active <https://docs.gtk.org/gtk4/property.Switch.active.html>`_, unless you are using the delayed state change feature described in `state-set <https://docs.gtk.org/gtk4/signal.Switch.state-set.html>`_.


.. _Diagnostic missing_descriptive_text:

missing_descriptive_text
~~~~~~~~~~~~~~~~~~~~~~~~
This widget has no text that would describe its purpose to a screen reader or other accessibility software. You should add a tooltip, or an accessibilty block:

.. code-block:: blueprint

   Image {
     accessibility {
       description: _("A cat jumping into a box");
     }
   }

If the widget is purely decorative, you can set the ``presentation`` accessibility role to hide it from accessibility software:

.. code-block:: blueprint

   Image {
     accessible-role: presentation;
   }


.. _Diagnostic missing_user_facing_text:

missing_user_facing_text
~~~~~~~~~~~~~~~~~~~~~~~~
This widget should have some text to display to the user to describe its function, such as a label or tooltip, but it doesn't.


.. _Diagnostic number_of_children:

number_of_children
~~~~~~~~~~~~~~~~~~
Some widgets can only have one child, and some cannot have any. Check the documentation for the widget you are using.

.. _Diagnostic scrollable_parent:

scrollable_parent
~~~~~~~~~~~~~~~~~
A widget that implements `Scrollable <https://docs.gtk.org/gtk4/iface.Scrollable.html>`_ should be a child of a `ScrolledWindow <https://docs.gtk.org/gtk4/class.ScrolledWindow.html>`_ or a `Adw.ClampScrollable <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.ClampScrollable.html>`_. Otherwise, it may not work correctly.

In particular, this setup with an `Adw.Clamp <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.Clamp.html>`_ is incorrect:

.. code-block:: blueprint
   :class: bad-example

   ScrolledWindow {
     Adw.Clamp {
       ListView {}
     }
   }

because the ListView's direct parent needs to provide scrolling for it. `Adw.ClampScrollable <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.6/class.ClampScrollable.html>`_ exists for this purpose:

.. code-block:: blueprint

   ScrolledWindow {
     Adw.ClampScrollable {
       ListView {}
     }
   }


.. _Diagnostic translate_display_string:

translate_display_string
~~~~~~~~~~~~~~~~~~~~~~~~
This property should usually be marked as translated.


.. _Diagnostic unused_object:

unused_object
~~~~~~~~~~~~~
This top-level object has no ID, so it can't be referenced elsewhere in the blueprint or the application.

.. note::
   Technically, it could be referenced in the application, since you can call `Gtk.Builder.get_objects() <https://docs.gtk.org/gtk4/method.Builder.get_objects.html>`_ to get all objects in the blueprint. However, this is not recommended, since it could break easily if you change the blueprint.


.. _Diagnostic use_adw_bin:

use_adw_bin
~~~~~~~~~~~
When using libadwaita, it is preferable to use `Adw.Bin <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.Bin.html>`_ for a container that only has one child, rather than a `Box <https://docs.gtk.org/gtk4/class.Box.html>`_, since ``Bin`` is specifically designed for this case.


.. _Diagnostic use_styles:

use_styles
~~~~~~~~~~
The `Widget:css-classes <https://docs.gtk.org/gtk4/property.Widget.css-classes.html>`_ property allows you to set the widget's CSS classes in an array. However, doing so overwrites any default classes the widget may set, which could make the styling look broken. Use the :ref:`styles<Syntax ExtStyles>` block instead, since it adds the classes to the existing list.


.. _Diagnostic use_unicode:

use_unicode
~~~~~~~~~~~
The text in a translated string should use Unicode characters where appropriate, such as “smart quotes” `GNOME Human Interface Guidelines <https://developer.gnome.org/hig/guidelines/typography.html>`_.


.. _Diagnostic wrong_parent:

wrong_parent
~~~~~~~~~~~~
Some object classes only have meaning inside a particular parent class. For example, a `StackPage <https://docs.gtk.org/gtk4/class.StackPage.html>`_ is a child of a `Stack <https://docs.gtk.org/gtk4/class.Stack.html>`_ and will not work elsewhere.


.. _Diagnostic visible_true:

visible_true
~~~~~~~~~~~~
In GTK 3, widgets were not visible by default, so you had to set ``visible: true`` on each one. However, in GTK 4,
the `visible <https://docs.gtk.org/gtk4/property.Widget.visible.html>` property defaults to ``true``, so this is no longer necessary.
