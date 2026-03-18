====================================
Advanced Expressions with BlueprintX
====================================

:ref:`Expressions <Syntax Expressions>` are a powerful way to link data and UI, but they have limited functionality by themselves. All calculations must be performed in application code using closures. This leads many application developers to write code like this:

.. code-block:: blueprint

   visible-child: bind $ternary(template.model as <Gio.ListStore>.n-items, "list", "empty-state");

This works, and many consider it cleaner than imperative code that pushes state updates from the application to the UI. However, it is still difficult to read and write. BlueprintX makes these expressions easier to write by adding new syntax for common operations. ``Note that you still have to implement the logic for these operations in your application code--BlueprintX just makes it easier to call that logic from expressions.``

To use BlueprintX features, pass the ``--blpx`` flag to the compiler. BlueprintX is still experimental and subject to change.

.. _Syntax BlueprintXExpression:

.. rst-class:: grammar-block

   Expression = Level1
   Level1 = Level2 ( '||' Level2 )*
   Level2 = Level3 ( '&&' Level3 )*
   Level3 = Level4 ( ('==' | '!=' | '<' | '>' | '<=' | '>=' ) Level4 )*
   Level4 = '-'? Level5 ( ('+' | '-') Level5 )*
   Level5 = Level6 ( ('*' | '/' | '%') Level6 )*
   Level6 = Level7 ( :ref:`CastExpression<Syntax CastExpression>` | :ref:`LookupExpression<Syntax LookupExpression>` )*
   Level7 = ( '!' Level8 ) | Level8
   Level8 = :ref:`ExpressionPrefix<Syntax ExpressionPrefix>`


.. _BlueprintX Operators:

+----------+-------------------------+
| Operator | Function                |
+==========+=========================+
| ||       | blpx_or                 |
+----------+-------------------------+
| &&       | blpx_and                |
+----------+-------------------------+
| ==       | blpx_eq_string, blpx_eq_float, blpx_eq_double, blpx_eq_int64, blpx_eq_uint64, blpx_eq_int, blpx_eq_uint |
+----------+-------------------------+
| !=       | blpx_ne_string, blpx_ne_float, blpx_ne_double, blpx_ne_int64, blpx_ne_uint64, blpx_ne_int, blpx_ne_uint |
+----------+-------------------------+
| <        | blpx_lt_string, blpx_lt_float, blpx_lt_double, blpx_lt_int64, blpx_lt_uint64, blpx_lt_int, blpx_lt_uint |
+----------+-------------------------+
| >        | blpx_gt_string, blpx_gt_float, blpx_gt_double, blpx_gt_int64, blpx_gt_uint64, blpx_gt_int, blpx_gt_uint |
+----------+-------------------------+
| <=       | blpx_le_string, blpx_le_float, blpx_le_double, blpx_le_int64, blpx_le_uint64, blpx_le_int, blpx_le_uint |
+----------+-------------------------+
| >=       | blpx_ge_string, blpx_ge_float, blpx_ge_double, blpx_ge_int64, blpx_ge_uint64, blpx_ge_int, blpx_ge_uint |
+----------+-------------------------+
| +        | blpx_add_string, blpx_add_float, blpx_add_double, blpx_add_int64, blpx_add_uint64, blpx_add_int, blpx_add_uint |
+----------+-------------------------+
| -        | blpx_sub_float, blpx_sub_double, blpx_sub_int64, blpx_sub_uint64, blpx_sub_int, blpx_sub_uint |
+----------+-------------------------+
| *        | blpx_mul_float, blpx_mul_double, blpx_mul_int64, blpx_mul_uint64, blpx_mul_int, blpx_mul_uint |
+----------+-------------------------+
| /        | blpx_div_float, blpx_div_double, blpx_div_int64, blpx_div_uint64, blpx_div_int, blpx_div_uint |
+----------+-------------------------+
| %        | blpx_mod_float, blpx_mod_double, blpx_mod_int64, blpx_mod_uint64, blpx_mod_int, blpx_mod_uint |
+----------+-------------------------+
| !        | blpx_not                |
+----------+-------------------------+