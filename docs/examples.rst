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

Use the ``sync-create`` keyword to cause a bound property to be initialized
when the UI is first constructed.

.. code-block::

   Gtk.ProgressBar bar1 {
     value: 10;
   }

   Gtk.ProgressBar bar2 {
     value: bind bar1.value sync-create;
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
       labelled_by: my_label;
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
