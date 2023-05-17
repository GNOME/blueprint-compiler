# v0.8.1

## Breaking Changes

- Duplicates in a number of places are now considered errors. For example, duplicate flags in several places, duplicate
  strings in Gtk.FileFilters, etc.

## Fixed

- Fixed a number of bugs in the XML output when using `template` to refer to the template object.

## Documentation

- Fixed the example for ExtListItemFactory

# v0.8.0

## Breaking Changes

- A trailing `|` is no longer allowed in flags.
- The primitive type names `gboolean`, `gchararray`, `gint`, `gint64`, `guint`, `guint64`, `gfloat`, `gdouble`, `utf8`, and `gtype` are no longer permitted. Use the non-`g`-prefixed versions instead.
- Translated strings may no longer have trailing commas.

## Added

- Added cast expressions, which are sometimes needed to specify type information in expressions.
- Added support for closure expressions.
- Added the `--typelib-path` command line argument, which allows adding directories to the search path for typelib files.
- Added custom compile and decompile commands to the language server. (Sonny Piers)
- Added support for [Adw.MessageDialog](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/class.MessageDialog.html#adwmessagedialog-as-gtkbuildable) custom syntax.
- Added support for inline sub-templates for [Gtk.BuilderListItemFactory](https://docs.gtk.org/gtk4/class.BuilderListItemFactory.html). (Cameron Dehning)
- Added support for [Adw.Breakpoint](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/class.Breakpoint.html) custom syntax.
- Added a warning when an object ID might be confusing.
- Added support for [Gtk.Scale](https://docs.gtk.org/gtk4/class.Scale.html#gtkscale-as-gtkbuildable) custom syntax.

## Changed

Some of these changes affect syntax, but the old syntax is still accepted with a purple "upgrade" warning, so they are not breaking changes yet. In editors that support code actions, such as Visual Studio Code, the blueprint language server can automatically fix these warnings.

- The XML output uses the integer value rather than GIR name for enum values.
- Compiler errors are now printed to stderr rather than stdout. (Sonny Piers)
- Introduced `$` to indicate types or callbacks that are provided in application code.
  - Types that are provided by application code are now begin with a `$` rather than a leading `.`.
  - The handler name in a signal is now prefixed with `$`.
  - Closure expressions, which were added in this version, are also prefixed with `$`.
- When a namespace is not found, errors are supressed when the namespace is used.
- The compiler bug message now reports the version of blueprint-compiler.
- The `typeof` syntax now uses `<>` instead of `()` to match cast expressions.
- Menu sections and subsections can now have an ID.
- The interactive porting tool now ignores hidden folders. (Sonny Piers)
- Templates now use the typename syntax rather than an ID to specify the template's class. In most cases, this just means adding a `$` prefix to the ID, but for GtkListItem templates it should be shortened to ListItem (since the Gtk namespace is implied). The template object is now referenced with the `template` keyword rather than with the ID.

## Fixed

- Fixed a bug in the language server's acceptance of text change commands. (Sonny Piers)
- Fixed a bug in the display of diagnostics when the diagnostic is at the beginning of a line.
- Fixed a crash that occurred when dealing with array types.
- Fixed a bug that prevented Gio.File properties from being settable.

## Documentation

- Added a reference section to the documentation. This replaces the Examples page with a detailed description of each syntax feature, including a formal specification of the grammar.

# v0.6.0

## Breaking Changes
- Quoted and numeric literals are no longer interchangeable (e.g. `"800"` is no longer an accepted value for an
  integer type).
- Boxed types are now type checked.

## Added
- There is now syntax for `GType` literals: the `typeof()` pseudo-function. For example, list stores have an `item-type`
  property which is now specifiable like this: `item-type: typeof(.MyDataModel)`. See the documentation for more details.

## Changed
- The language server now logs to stderr.

## Fixed
- Fix the build on Windows, where backslashes in paths were not escaped. (William Roy)
- Remove the syntax for specifying menu objects inline, since it does not work.
- Fix a crash in the language server that was triggered in files with incomplete `using Gtk 4.0;` statements.
- Fixed compilation on big-endian systems.
- Fix an issue in the interactive port tool that would lead to missed files. (Frank Dana)

## Documentation
- Fix an issue for documentation contributors where changing the documentation files would not trigger a rebuild.
- Document the missing support for Gtk.Label `<attributes>`, which is intentional, and recommend alternatives. (Sonny
  Piers)
- Add a prominent warning that Blueprint is still experimental


# v0.4.0

## Added
- Lookup expressions
- With the language server, hovering over a diagnostic message now shows any
  associated hints.

## Changed
- The compiler now uses .typelib files rather than XML .gir files, which reduces
  dependencies and should reduce compile times by about half a second.

## Fixed
- Fix the decompiler/porting tool not importing the Adw namespace when needed
- Fix a crash when trying to compile an empty file
- Fix parsing of number tokens
- Fix a bug where action widgets did not work in templates
- Fix a crash in the language server that occurred when a `using` statement had
no version
- If a compiler bug is reported, the process now exits with a non-zero code
