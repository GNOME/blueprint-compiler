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
