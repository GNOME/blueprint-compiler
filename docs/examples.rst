========
Examples
========


Namespaces and libraries
------------------------

GTK declaration
~~~~~~~~~~~~~~~

.. code-block::

   // Required in every blueprint file. Defines the major version
   // of GTK the file is designed for.
   using Gtk 4.0;

Importing libraries
~~~~~~~~~~~~~~~~~~~

.. code-block::

   // Import Adwaita 1. The name given here is the GIR namespace name, which
   // might not match the library name or C prefix.
   using Adw 1;


Objects
-------

Defining objects with properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

   Gtk.Box {
     orientation: vertical;

     Gtk.Label {
       label: "Hello, world!";
     }
   }

Referencing an object in code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

   // Your code can reference the object by `my_window`
   Gtk.Window my_window {
     title: "My window";
   }

Using classes defined by your app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a leading ``.`` to tell the compiler that the class is defined in your
app, not in the GIR, so it should skip validation.

.. code-block::

   .MyAppCustomWidget my_widget {
     my-custom-property: 3.14;
   }


Templates
---------

Defining a template
~~~~~~~~~~~~~~~~~~~

Many language bindings have a way to create subclasses that are defined both
in code and in the blueprint file. Check your language's documentation on
how to use this feature.

In this example, we create a class called ``MyAppWindow`` that inherits from
``Gtk.ApplicationWindow``.

.. code-block::

   template MyAppWindow : Gtk.ApplicationWindow {
     my-custom-property: 3.14;
   }

Referencing a template object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use a template object elsewhere in your blueprint, you can use
the template class name as the object ID:

.. code-block::

   template MyAppWindow : ApplicationWindow { }

   Gtk.Label {
     visible: bind MyAppWindow.visible;
   }


Properties
----------

Translations
~~~~~~~~~~~~

Use ``_("...")`` to mark strings as translatable. You can put a comment for
translators on the line above if needed.

.. code-block::

   Gtk.Label label {
     /* Translators: This is the main text of the welcome screen */
     label: _("Hello, world!");
   }

Use ``C_("context", "...")`` to add a *message context* to a string to
disambiguate it, in case the same string appears in different places. Remember,
two strings might be the same in one language but different in another depending
on context.

.. code-block::

   Gtk.Label label {
     /* Translators: This is a section in the preferences window */
     label: C_("preferences window", "Hello, world!");
   }

Referencing objects by ID
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

   Gtk.Range range1 {
     adjustment: my_adjustment;
   }
   Gtk.Range range2 {
     adjustment: my_adjustment;
   }

   Gtk.Adjustment my_adjustment {
   }

Defining object properties inline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

   Gtk.Range  {
     adjustment: Gtk.Adjustment my_adjustment {
       value: 10;
     };
   }

   Gtk.Range range1 {
     // You can even still reference the object by ID
     adjustment: my_adjustment;
   }

.. note::
   Note the semicolon after the closing brace of the ``Gtk.Adjustment``. It is
   required.

Type Literals
~~~~~~~~~~~~~

Some properties have the type `GObject.Type <https://docs.gtk.org/gobject/alias.Type.html>`_, that is, their value is
itself a description of a type in the GObject type system. An example is
`Gio.ListStore:item-type <https://docs.gtk.org/gio/property.ListStore.item-type.html>`_. Such properties can be
specified with the ``typeof()`` operator:

.. code-block::

   Gio.ListStore {
     item-type: typeof(.MyDataModel);
   }

.. note::

   Though it looks like a function, ``typeof()`` is actually a special operator. This is an important syntactic
   distinction because the argument to ``typeof()`` is interpreted at the grammar level as a type, not a value or
   expression.

Bindings
~~~~~~~~

Use the ``bind`` keyword to bind a property to another object's property in
the same file.

.. code-block::

   Gtk.ProgressBar bar1 {
   }

   Gtk.ProgressBar bar2 {
     value: bind bar1.value;
   }

Binding Flags
~~~~~~~~~~~~~

Use the ``no-sync-create`` keyword to only update the target value when the
source value changes, not when the binding is first created.

.. code-block::

   Gtk.ProgressBar bar1 {
     value: 10;
   }

   Gtk.ProgressBar bar2 {
     value: bind bar1.value no-sync-create;
   }

Use the ``bidirectional`` keyword to bind properties in both directions.

.. code-block::

   // Text of entry1 is bound to text
   // of entry2 and vice versa

   Gtk.Entry entry1 {
     text: bind entry2.text bidirectional;
   }

   Gtk.Entry entry2 {

   }

Use the ``inverted`` keyword to invert to bind a boolean property
to inverted value of another one.

.. code-block::

   // When switch1 is on, switch2 will be off
   Gtk.Switch switch1 {
     active: bind switch2.active inverted bidirectional;
   }

   // When switch2 is on, switch1 will be off
   Gtk.Switch switch2 {

   }


Signals
-------

Basic Usage
~~~~~~~~~~~

.. code-block::

   Gtk.Button {
     // on_button_clicked is defined in your application
     clicked => on_button_clicked();
   }

Flags
~~~~~

.. code-block::

   Gtk.Button {
     clicked => on_button_clicked() swapped;
   }

Object
~~~~~~

By default the widget is passed to callback as first argument. However,
you can specify another object to use as first argument of callback.

.. code-block::

   Gtk.Entry {
     activate => grab_focus(another_entry);
   }

   Gtk.Entry another_entry {

   }


CSS Styles
----------

Basic Usage
~~~~~~~~~~~

.. code-block::

   Gtk.Label {
     styles ["dim-label", "title"]
   }


Menus
-----

Basic Usage
~~~~~~~~~~~

.. code-block::

   menu my_menu {
     section {
       label: _("File");
       item {
         label: _("Open");
         action: "win.open";
       }
       item {
         label: _("Save");
         action: "win.save";
       }
       submenu {
         label: _("Save As");
         item {
           label: _("PDF");
           action: "win.save_as_pdf";
         }
       }
     }
   }

Item Shorthand
~~~~~~~~~~~~~~

For menu items with only a label, action, and/or icon, you can define all three
on one line. The action and icon are optional.

.. code-block::

   menu {
     item (_("Copy"), "app.copy", "copy-symbolic")
   }


Layout Properties
-----------------

Basic Usage
~~~~~~~~~~~

.. code-block::

   Gtk.Grid {
     Gtk.Label {
       layout {
         row: 0;
         column: 1;
       }
     }
   }


Accessibility Properties
------------------------

Basic Usage
~~~~~~~~~~~

.. code-block::

   Gtk.Widget {
     accessibility {
       orientation: vertical;
       labelled-by: my_label;
       checked: true;
     }
   }

   Gtk.Label my_label {}


Widget-Specific Items
---------------------

Gtk.ComboBoxText
~~~~~~~~~~~~~~~~

.. code-block::

   Gtk.ComboBoxText {
     items [
       item1: "Item 1",
       item2: _("Items can be translated"),
       "The item ID is not required",
     ]
   }

Gtk.FileFilter
~~~~~~~~~~~~~~

.. code-block::

   Gtk.FileFilter {
     mime-types ["image/jpeg", "video/webm"]
     patterns ["*.txt"]
     suffixes ["png"]
   }

Gtk.SizeGroup
~~~~~~~~~~~~~

.. code-block::

   Gtk.SizeGroup {
     mode: both;
     widgets [label1, label2]
   }

   Gtk.Label label1 {}
   Gtk.Label label2 {}

Gtk.StringList
~~~~~~~~~~~~~~

.. code-block::

   Gtk.StringList {
     strings ["Hello, world!", _("Translated string")]
   }

Gtk.Dialog and Gtk.InfoBar
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

   Gtk.Dialog {
     [action response=ok]
     Gtk.Button ok_response {}

     [action response=cancel]
     Gtk.Button cancel_response {}

     [action response=9]
     Gtk.Button app_defined_response {}
   }

Gtk.Label
~~~~~~~~~

Blueprint does not have syntax for `attributes` on `Gtk.Label`.

Instead, you should use `platform classes <https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/style-classes.html>`_, `CSS <https://docs.gtk.org/gtk4/css-properties.html>`_, `Pango Markup <https://docs.gtk.org/Pango/pango_markup.html>`_ or `Gtk.Label.set_attributes <https://docs.gtk.org/gtk4/method.Label.set_attributes.html>`_.

Examples

.. code-block::

   Gtk.Label {
     label: "Hello, World!";
     styles ["title-1"]
   }

.. code-block::

   Gtk.Label {
     label: "<b>Hello, World!</b>";
     use-markup: true;
   }
