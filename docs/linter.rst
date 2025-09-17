======
Linter
======

Blueprint files can be linted with the Blueprint Compiler.
For a single file to be linted use:

.. code-block::

   python blueprint-compiler.py lint <file1.blp>

For checking multiple files, just add them to the above command like this:

.. code-block::

   python blueprint-compiler.py lint <file1.blp> <file2.blp> <file3.blp>

An entire dirctory can also be scanned by specifiying the folder location:

.. code-block::

   python blueprint-compiler.py lint test/directory/location/

Contexts
--------

The linter is intended to flag issues related to accessibility, best practices, and logical errors.
The development of the linter is still ongoing so new rules and features are being added in the future.

Following are some examples of the linter rules that have been implemented so far.

Accessibility Rules
-------------------

Missing user-facing text properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: missing_user_facing_properties
**Details**: Properties are required for each element declared. For example components such as Label:label, Entry:placeholder should use appropriate human readable text, and follow typography from GNOME HIG.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   Button {
   }
   Entry {
   }

Examples of **correct** code for this rule:

.. code-block:: blueprint

   Button {
      label: _("Submit");
   }
   Entry {
      placeholder-text: _("Enter username");
   }

Avoid all caps
~~~~~~~~~~~~~~

**Rule**: avoid_all_caps
**Details**: The use of caps should be avoided in user facing texts.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

  Button {
    label: _("SUBMIT");
  }


Examples of **correct** code for this rule:

.. code-block:: blueprint

  Button {
    label: _("Submit");
  }

Warn against ASCII characters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: prefer_unicode_chars
**Details**: Unicode is preferred over ASCII characters whenever possible.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   // Using ASCII characters
   Label {
      label: _("Click "OK"");
   }

Examples of **correct** code for this rule:

.. code-block:: blueprint

   // Using Unicode
   Label {
      label: _("Click “OK”");
   }

Logical Rules
-------------

No child or single child allowed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: number_of_children
**Details**: Passing children to objects that don't accept any, such as Label, will not provide any feedback. It is confusing for beginners as the children don't get rendered but no explanation is given. In addition some widgets like AdwStatusPage, Adw.Clamp, ScrolledWindow etc. allow only one child. Only the last child will be rendered.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   // No child allowed
   Label {
      label: "Hello";
         Button {
            label: "World";
         }
   }

   // Single child allowed
   Adw.StatusPage {
      Button {
         label: "a";
      }

      Button {
         label: "b";
      }
   }

Examples of **correct** code for this rule:

.. code-block:: blueprint

   // No child allowed
   Label {
      label: "Hello";
   }

   // Single child allowed
   Adw.StatusPage {
      Button {
         label: "a";
      }
   }

Order of properties on Gtk.Adjustment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: order_properties_gtk_adjustment
**Details**:  Warn if Gtk.Adjustment properties are declared out of order (lower, upper, and then value).

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   Scale one {
      width-request: 130;
      adjustment: Adjustment {
         lower: 0;
         value: 50;
         upper: 100;
      };
   }


Examples of **correct** code for this rule:

.. code-block:: blueprint

   Scale one {
      width-request: 130;
      adjustment: Adjustment {
         lower: 0;
         upper: 100;
         value: 50;
      };
   }

Miscellaneous Rules
-------------------

Wrap user visible strings with _(...)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: translatable_display_string
**Details**:  User visible strings should be marked as translatable using _(...)

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   Label {
      label: "foo";
   }
   Button {
      tooltip-text: "foo";
   }
   Window {
      title: "foobar";
   }

Examples of **correct** code for this rule:

.. code-block:: blueprint

   Label {
      label: _("foo");
   }
   Button {
      tooltip-text: _("foo");
   }
   Window {
      title: _("foobar");
   }

Discourage css-classes usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: use_styles_over_css_classes
**Details**: Promotes the use of `styles` array instead of `css-classes` which overrides default classes.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   Box {
      orientation: vertical;
      overflow: hidden;
      css-classes: ["shadowed"];
   }

Examples of **correct** code for this rule:

.. code-block:: blueprint

   Box {
      orientation: vertical;
      overflow: hidden;
      styles [
         "Card",
         "translation-side-box",
      ]
   }

Warn on unused widgets
~~~~~~~~~~~~~~~~~~~~~~

**Rule**: incorrect_widget_placement
**Details**:  A widget is declared but not used under an appropriate parent widget.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   // If this widget is declared but never added to a container (Box, Window, etc.). It's invisible and unused.

   Label {
      label: _("Info")
   }


Examples of **correct** code for this rule:

.. code-block:: blueprint

   // Label is part of a Box and Window which is rendered on a screen.

   @template Window
   window ApplicationWindow {
      default-width: 300
      default-height: 100
      title: _("Used widget")

      Box {
         orientation: vertical
         spacing: 6

         Label {
            label: _("Info")
         }
      }
   }


Clamp in ScrolledWindow warning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule**: clamp_scrolledwindow
**Details**: Clamp should be used as a child property to ScrolledWindow for proper scroll behavior.

Examples of **incorrect** code for this rule:

.. code-block:: blueprint

   ScrolledWindow {
      child: Adw.Clamp {
         child: Box {
            Label {
            label: _("This is incorrect");
            }
         }
      }


Examples of **correct** code for this rule:

.. code-block:: blueprint

   Adw.Clamp {
      child: ScrolledWindow {
         child: Box {
            Label {
            label: _("This is correct");
            }
         }
      }
   }
