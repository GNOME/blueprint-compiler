====================
Advanced Expressions
====================

:ref:`Expressions <Syntax Expression>` are a powerful way to link data and UI, but they have limited functionality by themselves. All calculations must be performed in application code using closures. This leads many application developers to write code like this:

.. code-block:: blueprint

   visible-child: bind $ternary(template.model as <Gio.ListStore>.n-items, "list", "empty-state");

This works, and many consider it cleaner than imperative code that pushes state updates from the application to the UI. However, it is still difficult to read and write. Advanced expressions make these expressions easier by adding new syntax for common operations. ``Note that you still have to implement the logic for these operations in your application code--advanced expressions just make it easier to call that logic from expressions.``

To use advanced expressions, pass the ``--expressions=blpx`` or ``--expressions=blpx-dynamic`` flag to the compiler. Advanced expressions are still experimental and subject to change.

.. _Syntax AdvancedExpression:

Advanced Expressions
--------------------

.. rst-class:: grammar-block

   Expression = Level1
   Level1 = Level2 ( '||' Level2 )*
   Level2 = Level3 ( '&&' Level3 )*
   Level3 = Level4 ( ('==' | '!=' | '<' | '>' | '<=' | '>=' ) Level4 )*
   Level4 = '-'? Level5 ( ('+' | '-') Level5 )*
   Level5 = Level6 ( ('*' | '/' | '%') Level6 )*
   Level6 = Level7 ( :ref:`CastExpression<Syntax CastExpression>` | :ref:`LookupExpression<Syntax LookupExpression>` )*
   Level7 = ( '!' Level8 ) | Level8
   Level8 = IfExpression | :ref:`ExpressionPrefix<Syntax Expression>`
   IfExpression = 'if' '{' Expression '}' ( 'elif' '{' Expression '}' )* 'else' '{' Expression '}'


.. _Closure Specifications:

========== ========================== ===================== =======
 Operator   Signature                  Function              T
========== ========================== ===================== =======
 ``||``     ``(bool, bool) -> bool``   ``blpx_or``
 ``&&``     ``(bool, bool) -> bool``   ``blpx_and``
 ``if``     ``(bool, T, T) -> T``      ``blpx_if`` [1]_      ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``, ``bool``, ``ptr``
 ``==``     ``(T, T) -> bool``         ``blpx_eq``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``, ``bool``, ``ptr``
 ``!=``     ``(T, T) -> bool``         ``blpx_ne``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``, ``bool``, ``ptr``
 ``<``     ``(T, T) -> bool``          ``blpx_lt``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``>``     ``(T, T) -> bool``          ``blpx_gt``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``<=``     ``(T, T) -> bool``         ``blpx_le``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``>=``     ``(T, T) -> bool``         ``blpx_ge``           ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``+``     ``(T, T) -> T``             ``blpx_add``          ``string``, ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``-``     ``(T, T) -> T``             ``blpx_sub``          ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``-``     ``(T) -> T``                ``blpx_neg``          ``float``, ``double``, ``int64``, ``int``
 ``*``     ``(T, T) -> T``             ``blpx_mul``          ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``/``     ``(T, T) -> T``             ``blpx_div``          ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``%``     ``(T, T) -> T``             ``blpx_mod``          ``float``, ``double``, ``int64``, ``uint64``, ``int``, ``uint``
 ``!``     ``(bool) -> bool``          ``blpx_not``
========== ========================== ===================== =======

.. [1] ``blpx_if`` is the ternary operator. The first argument is the condition, the second argument is the value if the condition is true, and the third argument is the value if the condition is false. ``elif`` clauses are compiled to nested ``blpx_if`` closures.

.. _Static vs. Dynamic Closures:

Some application languages are dynamically typed, meaning that the type of a variable is determined at runtime rather than at compile time. In these languages, such as Python, a single closure can operate on values many different types:

.. code-block:: python

   def blpx_add(a, b):
       return a + b

   print(blpx_add(1, 2))         # Works with integers
   print(blpx_add(1.5, 2.5))     # Works with floats
   print(blpx_add("foo", "bar")) # Works with strings
   print(blpx_add(1.5, 2.5))     # Even works with a mix of numeric types

However, in statically typed languages like C, multiple closures would be needed, one for each type:

.. code-block:: c

   static int
   blpx_add_int(int a, int b) {
     return a + b;
   }

   static double
   blpx_add_double(double a, double b) {
     return a + b;
   }

   static char *
   blpx_add_string(const char* a, const char* b) {
     return g_strconcat(a, b, NULL);
   }

Blueprint has two modes for handling types in closures. With ``--expressions=blpx``, closures are suffixed with the type they operate on (noted as ``T`` in the table above). With ``--expressions=blpx-dynamic``, closures are not suffixed and are expected to handle types dynamically.

The following closures perform numeric type casting. This is only necessary in static mode and is used to implement operations with mixed input types.

=========== =========
 Cast From   Cast To
=========== =========
 ``int64``   ``uint64``, ``double``
 ``uint64``  ``int64``, ``double``
 ``int``     ``int64``, ``double``
 ``uint``    ``int``, ``uint64``, ``double``
 ``float``   ``double``
=========== =========

For example, ``blpx_cast_int64_double`` casts an ``int64`` value to a ``double``.
