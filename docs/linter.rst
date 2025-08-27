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


Contexts
--------

The linter is intended to flag issues related to accessibility, best practices, and logical errors.
The development of the linter is still ongoing so new rules and features are being added in the future.


