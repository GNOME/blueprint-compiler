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
