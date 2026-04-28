====================
Advanced Expressions
====================

:ref:`Expressions <Syntax Expression>` are a powerful way to link data and UI, but they have limited functionality by themselves. All calculations must be performed in application code using closures. This leads many application developers to write code like this:

.. code-block:: blueprint

   visible-child: bind $ternary(template.model as <Gio.ListStore>.n-items, "list", "empty-state");

This works, and many consider it cleaner than imperative code that pushes state updates from the application to the UI. However, it is still difficult to read and write. Advanced expressions make these expressions easier by adding new syntax for common operations. ``Note that you still have to implement the logic for these operations in your application code--advanced expressions just make it easier to call that logic from expressions.``

To use advanced expressions, pass the ``--blpx`` flag to the compiler. Advanced expressions are still experimental and subject to change.

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

========== ============ =============
 Operator   Arity [1]_   Function(s)
========== ============ =============
 ``||``         2            ``blpx_or``
 ``&&``         2            ``blpx_and``
 ``if``         3            ``blpx_if`` [2]_
 ``==``         2            ``blpx_eq_string``, ``blpx_eq_float``, ``blpx_eq_double``, ``blpx_eq_int64``, ``blpx_eq_uint64``, ``blpx_eq_int``, ``blpx_eq_uint``
 ``!=``         2            ``blpx_ne_string``, ``blpx_ne_float``, ``blpx_ne_double``, ``blpx_ne_int64``, ``blpx_ne_uint64``, ``blpx_ne_int``, ``blpx_ne_uint``
 ``<``          2            ``blpx_lt_string``, ``blpx_lt_float``, ``blpx_lt_double``, ``blpx_lt_int64``, ``blpx_lt_uint64``, ``blpx_lt_int``, ``blpx_lt_uint``
 ``>``          2            ``blpx_gt_string``, ``blpx_gt_float``, ``blpx_gt_double``, ``blpx_gt_int64``, ``blpx_gt_uint64``, ``blpx_gt_int``, ``blpx_gt_uint``
 ``<=``         2            ``blpx_le_string``, ``blpx_le_float``, ``blpx_le_double``, ``blpx_le_int64``, ``blpx_le_uint64``, ``blpx_le_int``, ``blpx_le_uint``
 ``>=``         2            ``blpx_ge_string``, ``blpx_ge_float``, ``blpx_ge_double``, ``blpx_ge_int64``, ``blpx_ge_uint64``, ``blpx_ge_int``, ``blpx_ge_uint``
 ``+``          2            ``blpx_add_string``, ``blpx_add_float``, ``blpx_add_double``, ``blpx_add_int64``, ``blpx_add_uint64``, ``blpx_add_int``, ``blpx_add_uint``
 ``-``          2            ``blpx_sub_float``, ``blpx_sub_double``, ``blpx_sub_int64``, ``blpx_sub_uint64``, ``blpx_sub_int``, ``blpx_sub_uint``
 ``-``          1            ``blpx_neg_float``, ``blpx_neg_double``, ``blpx_neg_int64``, ``blpx_neg_uint64``, ``blpx_neg_int``, ``blpx_neg_uint``
 ``*``          2            ``blpx_mul_float``, ``blpx_mul_double``, ``blpx_mul_int64``, ``blpx_mul_uint64``, ``blpx_mul_int``, ``blpx_mul_uint``
 ``/``          2            ``blpx_div_float``, ``blpx_div_double``, ``blpx_div_int64``, ``blpx_div_uint64``, ``blpx_div_int``, ``blpx_div_uint``
 ``%``          2            ``blpx_mod_float``, ``blpx_mod_double``, ``blpx_mod_int64``, ``blpx_mod_uint64``, ``blpx_mod_int``, ``blpx_mod_uint``
 ``!``          1            ``blpx_not``
========== ============ =============

.. [1] Arity is the number of arguments an operator takes.
.. [2] ``blpx_if`` is the ternary operator. The first argument is the condition, the second argument is the value if the condition is true, and the third argument is the value if the condition is false. ``elif`` clauses are compiled to nested ``blpx_if`` closures.

Some closure names are suffixed with a type, such as ``blpx_eq_string``. These closures must convert their arguments to the specified type before performing the operation. For example, ``blpx_eq_string`` converts both of its arguments to strings, then compares them. ``blpx_mul_float`` converts both of its arguments to floats, multiplies them, and returns the result as a float.
