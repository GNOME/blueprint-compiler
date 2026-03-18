# expressions.py
#
# Copyright 2022 James Westman <james@jwestman.net>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later


from functools import cached_property

from ..decompiler import decompile_element, full_name
from ..utils import TextEdit
from .common import *
from .contexts import ScopeCtx, ValueTypeCtx
from .translated import *
from .types import TypeName

expr = Sequence()


class ExprBase(AstNode):
    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        if container := self.containing_expression:
            return container.context[ValueTypeCtx]
        else:
            return self.parent.context[ValueTypeCtx]

    @property
    def type(self) -> T.Optional[GirType]:
        raise NotImplementedError()

    @property
    def containing_expression(self) -> T.Optional["InfixExpr"]:
        if isinstance(self.parent, Expression):
            children = list(self.parent.children)
            if children.index(self) + 1 < len(children):
                child = children[children.index(self) + 1]
                assert isinstance(child, InfixExpr)
                return child
            else:
                return self.parent.containing_expression
        elif isinstance(self.parent, InfixExpr):
            return self.parent
        else:
            return None

    @property
    def left_expression(self):
        if isinstance(self.parent, InfixExpr):
            return self.parent
        elif isinstance(self.parent, Expression):
            return self.parent.left_expression
        else:
            return None

    @property
    def right_expression(self):
        if isinstance(self.parent, InfixExpr):
            return self.parent.containing_expression
        elif isinstance(self.parent, Expression):
            return self.containing_expression
        else:
            return None


class Expression(ExprBase):
    """An Expression contains a prefix node and optionally some infix operators."""

    grammar: T.Any = expr

    @property
    def last(self) -> ExprBase:
        last = self.children[-1]
        if isinstance(last, Expression):
            return last.last
        else:
            return last

    @property
    def type(self) -> T.Optional[GirType]:
        return self.last.type

    @property
    def is_stub(self) -> bool:
        return len(self.children) == 1 and isinstance(self.children[0], Expression)

    @validate()
    def validate_for_type(self):
        if self.is_stub:
            # Avoid duplicate errors on expressions that just wrap another expression
            return

        expected_type = self.context[ValueTypeCtx].value_type
        if self.type is not None and expected_type is not None:
            if not self.type.assignable_to(expected_type):
                if not isinstance(self.containing_expression, CastExpr):
                    castable = (
                        " without casting"
                        if self.type.castable_to(expected_type)
                        else ""
                    )
                    raise CompileWarning(
                        f"Cannot assign {self.type.full_name} to {expected_type.full_name}{castable}"
                    )

    @autofix
    def autofix_cast(self):
        if self.is_stub:
            return []

        expected_type = self.parent.context[ValueTypeCtx].value_type
        if self.type is not None and expected_type is not None:
            if not self.type.assignable_to(expected_type):
                if self.type.castable_to(expected_type):
                    range = Range(
                        self.range.end, self.range.end, self.range.original_text
                    )
                    return [TextEdit(range, f" as <{expected_type.full_name}>")]

        return []


class InfixExpr(ExprBase):
    @property
    def lhs(self):
        children = list(self.parent_by_type(Expression).children)
        index = children.index(self)
        if index == 0:
            return self.parent_by_type(Expression).left_expression
        else:
            prev = children[index - 1]
            if isinstance(prev, Expression):
                return prev.last
            else:
                assert isinstance(prev, ExprBase)
                return prev


class LiteralExpr(ExprBase):
    grammar = LITERAL

    @property
    def is_object(self) -> bool:
        from .values import IdentLiteral

        return isinstance(self.literal.value, IdentLiteral) and (
            self.literal.value.ident in self.context[ScopeCtx].objects
            or self.root.is_legacy_template(self.literal.value.ident)
        )

    @property
    def is_this(self) -> bool:
        from .values import IdentLiteral

        return (
            not self.is_object
            and isinstance(self.literal.value, IdentLiteral)
            and self.literal.value.ident == "item"
        )

    @property
    def literal(self):
        from .values import Literal

        return self.children[Literal][0]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.literal.value.type

    @validate()
    def item_validations(self):
        if self.is_this:
            if not isinstance(self.containing_expression, CastExpr):
                raise CompileError('"item" must be cast to its object type')

            if not isinstance(
                self.containing_expression.containing_expression, LookupOp
            ):
                raise CompileError('"item" can only be used for looking up properties')


class TranslatedExpr(ExprBase):
    grammar = Translated

    @property
    def translated(self) -> Translated:
        return self.children[Translated][0]

    @property
    def type(self) -> GirType:
        return StringType()


class LookupOp(InfixExpr):
    grammar = [".", UseIdent("property")]
    precedence = 6

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(None, must_infer_type=True)

    @property
    def property_name(self) -> str:
        return self.tokens["property"]

    @property
    def type(self) -> T.Optional[GirType]:
        if isinstance(self.lhs.type, gir.Class) or isinstance(
            self.lhs.type, gir.Interface
        ):
            if property := self.lhs.type.properties.get(self.property_name):
                return property.type

        return None

    @docs("property")
    def property_docs(self):
        if not (
            isinstance(self.lhs.type, gir.Class)
            or isinstance(self.lhs.type, gir.Interface)
        ):
            return None

        if property := self.lhs.type.properties.get(self.property_name):
            return property.doc

    @validate("property")
    def property_exists(self):
        if self.lhs.type is None:
            # Literal values throw their own errors if the type isn't known
            if isinstance(self.lhs, LiteralExpr):
                return

            raise CompileError(
                f"Could not determine the type of the preceding expression",
                hints=[
                    f"add a type cast so blueprint knows which type the property {self.property_name} belongs to"
                ],
            )

        if self.lhs.type.incomplete:
            return

        elif not isinstance(self.lhs.type, gir.Class) and not isinstance(
            self.lhs.type, gir.Interface
        ):
            raise CompileError(
                f"Type {self.lhs.type.full_name} does not have properties"
            )

        elif self.lhs.type.properties.get(self.property_name) is None:
            raise CompileError(
                f"{self.lhs.type.full_name} does not have a property called {self.property_name}",
                did_you_mean=(self.property_name, self.lhs.type.properties.keys()),
            )

    @validate("property")
    def property_deprecated(self):
        if self.lhs.type is None or not (
            isinstance(self.lhs.type, gir.Class)
            or isinstance(self.lhs.type, gir.Interface)
        ):
            return

        if property := self.lhs.type.properties.get(self.property_name):
            if property.deprecated:
                hints = []
                if property.deprecated_doc:
                    hints.append(property.deprecated_doc)
                raise DeprecatedWarning(
                    f"{property.signature} is deprecated",
                    hints=hints,
                )


class CastExpr(InfixExpr):
    grammar = [
        Keyword("as"),
        AnyOf(
            ["<", to_parse_node(TypeName).expected("type name"), Match(">").expected()],
            [
                UseExact("lparen", "("),
                TypeName,
                UseExact("rparen", ")").expected("')'"),
            ],
        ),
    ]
    precedence = 6

    @context(ValueTypeCtx)
    def value_type(self):
        return ValueTypeCtx(self.type, allow_null=True)

    @property
    def type(self) -> T.Optional[GirType]:
        return self.children[TypeName][0].gir_type

    @validate()
    def cast_makes_sense(self) -> None:
        if self.type is None or self.lhs.type is None:
            return

        if not self.type.castable_to(self.lhs.type) and not self.lhs.type.castable_to(
            self.type
        ):
            raise CompileError(
                f"Invalid cast. No instance of {self.lhs.type.full_name} can be an instance of {self.type.full_name}."
            )

    @validate("lparen", "rparen")
    def upgrade_to_angle_brackets(self):
        if self.tokens["lparen"]:
            raise UpgradeWarning(
                "Use angle bracket syntax introduced in blueprint 0.8.0",
                actions=[
                    CodeAction(
                        "Use <> instead of ()",
                        f"<{self.children[TypeName][0].as_string}>",
                    )
                ],
            )

    @docs("as")
    def ref_docs(self):
        return get_docs_section("Syntax CastExpression")

    @autofix
    def autofix_unnecessary_cast(self):
        if self.type is None:
            return []

        expected_type = self.parent.context[ValueTypeCtx].value_type
        if (
            expected_type is not None
            and self.type.assignable_to(expected_type)
            and expected_type.assignable_to(self.type)
        ):
            return [TextEdit(self.range.with_preceding_whitespace, "")]
        else:
            return []


class ClosureArg(AstNode):
    grammar = Expression

    @property
    def expr(self) -> Expression:
        return self.children[Expression][0]

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(None, must_infer_type=True, allow_null=True)


class ClosureExpr(ExprBase):
    grammar = [
        Optional(["$", UseLiteral("extern", True)]),
        UseIdent("name"),
        "(",
        Delimited(ClosureArg, ","),
        ")",
    ]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.context[ValueTypeCtx].value_type

    @property
    def closure_name(self) -> str:
        return self.tokens["name"]

    @property
    def args(self) -> T.List[ClosureArg]:
        return self.children[ClosureArg]

    @validate()
    def return_type_known(self):
        if self.type is None:
            raise CompileError(
                "Closure expression must be cast to the closure's return type",
                hints=[
                    "The return type of this closure cannot be inferred, so you must add a type cast to indicate the return type."
                ],
            )

    @validate()
    def builtin_exists(self):
        if not self.tokens["extern"]:
            raise CompileError(f"{self.closure_name} is not a builtin function")

    @docs("name")
    def ref_docs(self):
        return get_docs_section("Syntax ClosureExpression")


class TryExpr(ExprBase):
    grammar = [
        Keyword("try"),
        UseExact("lbrace", "{"),
        Delimited(Expression, ","),
        UseExact("rbrace", "}").expected("'}'"),
    ]

    @property
    def expressions(self) -> T.List[Expression]:
        return self.children[Expression]

    @cached_property
    def type(self) -> T.Optional[GirType]:
        return None

    @docs("try")
    def ref_docs(self):
        return get_docs_section("Syntax TryExpression")

    @validate()
    def at_least_one_expression(self):
        exprs = self.children[Expression]
        if len(exprs) == 0:
            raise CompileError("A try expression must have at least one branch")

    @validate("try")
    def at_least_two_expressions(self):
        exprs = self.children[Expression]
        if len(exprs) < 2:
            raise CompileWarning(
                "This try expression has only one branch",
                actions=[
                    CodeAction(
                        "Remove try",
                        "",
                        additional_edits=[
                            TextEdit(self.ranges["lbrace"], ""),
                            TextEdit(self.ranges["rbrace"], ""),
                        ],
                    )
                ],
            )

    @validate()
    def expressions_have_same_type(self):
        if len(self.expressions) < 2:
            return

        types = [expr.type for expr in self.expressions]
        if None in types:
            return None

        t = GirType.common_ancestor(T.cast(T.List[GirType], types))

        if t is None:
            raise CompileError(
                "All branches of a try expression must have compatible types"
            )


class OpExpr(InfixExpr):
    @property
    def closure_name(self) -> str:
        raise NotImplementedError()

    @property
    def args(self) -> T.List[ExprBase]:
        raise NotImplementedError()

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(None, must_infer_type=True)

    @validate()
    def blpx_enabled(self):
        # Only emit this error on top-level expressions, to avoid duplicate errors on sub-expressions
        parent = self.parent
        while parent is not None:
            if isinstance(parent, OpExpr):
                return
            parent = parent.parent

        if not self.root.blpx_enabled:
            raise CompileError(
                f"Enable --blpx to use advanced expression features",
                range=Range(
                    self.lhs.range.start if self.lhs is not None else self.range.start,
                    self.range.end,
                    self.range.original_text,
                ),
            )


class Parenthesized(ExprBase):
    grammar = [
        UseExact("lparen", "("),
        Expression,
        UseExact("rparen", ")").expected("')'"),
    ]

    @property
    def child(self) -> Expression:
        return self.children[Expression][0]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.child.type

    @autofix
    def autofix_redundant_parentheses(self):
        redundant = False

        left = self.left_expression
        right = self.right_expression

        if not hasattr(self.child.last, "precedence"):
            redundant = True
        elif (
            left is not None
            and hasattr(left, "precedence")
            and left.precedence < self.child.last.precedence
        ):
            redundant = True
        elif (
            right is not None
            and hasattr(right, "precedence")
            and right.precedence < self.child.last.precedence
        ):
            redundant = True

        if redundant:
            return [
                TextEdit(self.ranges["lparen"], ""),
                TextEdit(self.ranges["rparen"], ""),
            ]
        else:
            return []


def precedence(g) -> T.Type[Expression]:
    class Precedence(Expression):
        grammar = g

    return Precedence


class UnaryOpExpr(OpExpr):
    @property
    def args(self) -> T.List[ExprBase]:
        return self.children


class BinaryOpExpr(OpExpr):
    @property
    def args(self) -> T.List[ExprBase]:
        return [self.lhs, *self.children]

    @property
    def rhs(self) -> ExprBase:
        return self.children[-1]

    @property
    def type(self):
        if self.lhs is None or self.rhs is None:
            return None

        lhs_type = self.lhs.type
        rhs_type = self.rhs.type

        if isinstance(lhs_type, StringType) and isinstance(rhs_type, StringType):
            return StringType()
        elif isinstance(lhs_type, NumericType) and isinstance(rhs_type, NumericType):
            if lhs_type.floating or rhs_type.floating:
                if max(lhs_type.size, rhs_type.size) <= 32:
                    return FloatType()
                else:
                    return DoubleType()
            elif lhs_type.signed or rhs_type.signed:
                if max(lhs_type.size, rhs_type.size) <= 32:
                    return IntType(32, signed=True)
                else:
                    return IntType(64, signed=True)
            else:
                if max(lhs_type.size, rhs_type.size) <= 32:
                    return IntType(32, signed=False)
                else:
                    return IntType(64, signed=False)

        return None

    def require_numeric_operands(self, operator: str):
        lhs_numeric = isinstance(self.lhs.type, NumericType)
        rhs_numeric = isinstance(self.rhs.type, NumericType)

        if self.lhs.type is None:
            # Literal values throw their own errors if the type isn't known
            if isinstance(self.lhs, LiteralExpr):
                return

            raise CompileError(
                f"Could not determine the type of this expression", range=self.lhs.range
            )
        elif self.rhs.type is None:
            if isinstance(self.rhs, LiteralExpr):
                return

            raise CompileError(
                f"Could not determine the type of this expression", range=self.rhs.range
            )
        elif not lhs_numeric and not rhs_numeric:
            raise CompileError(
                f"Cannot apply {operator} to non-numeric types {self.lhs.type.full_name} and {self.rhs.type.full_name}",
                Range(self.lhs.range.start, self.range.end, self.range.original_text),
            )
        elif not lhs_numeric:
            raise CompileError(
                f"Cannot apply {operator} to non-numeric type {self.lhs.type.full_name}",
                Range(
                    self.lhs.range.start,
                    self.ranges["after_op"].end,
                    self.range.original_text,
                ),
            )
        elif not rhs_numeric:
            raise CompileError(
                f"Cannot apply {operator} to non-numeric type {self.rhs.type.full_name}",
                self.range,
            )


lvl8 = precedence(
    AnyOf(TranslatedExpr, TryExpr, ClosureExpr, LiteralExpr, Parenthesized)
)


class NotExpr(UnaryOpExpr):
    grammar = [Keyword("!"), lvl8]
    closure_name = "blpx_not"
    precedence = 7
    type = BoolType()

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(BoolType())

    @validate()
    def boolean_operand(self):
        operand = self.children[0]
        if not isinstance(operand.type, BoolType):
            raise CompileError(
                f"Cannot apply ! to non-boolean type {operand.type.full_name}",
                Range(operand.range.start, self.range.end, self.range.original_text),
            )


lvl7 = precedence(AnyOf(NotExpr, lvl8))

lvl6 = precedence([lvl7, ZeroOrMore(AnyOf(CastExpr, LookupOp))])


class MulExpr(BinaryOpExpr):
    grammar = [
        AnyOf(Keyword("*"), Keyword("/"), Keyword("%")),
        Mark("after_op"),
        lvl6,
    ]
    precedence = 5

    @property
    def closure_name(self) -> str:
        if self.tokens["*"]:
            op = "mul"
        elif self.tokens["/"]:
            op = "div"
        elif self.tokens["%"]:
            op = "mod"
        return f"blpx_{op}_{self.type.glib_type_name}"

    @validate()
    def numeric_operands(self):
        operator = ""
        if self.tokens["*"]:
            operator = "*"
        elif self.tokens["/"]:
            operator = "/"
        elif self.tokens["%"]:
            operator = "%"
        self.require_numeric_operands(operator)


lvl5 = precedence([lvl6, ZeroOrMore(MulExpr)])


class AddExpr(BinaryOpExpr):
    grammar = [AnyOf(Keyword("+"), Keyword("-")), lvl5]
    precedence = 4

    @property
    def closure_name(self) -> str:
        if self.tokens["+"]:
            op = "add"
        elif self.tokens["-"]:
            op = "sub"
        return f"blpx_{op}_{self.type.glib_type_name}"

    @property
    def is_string_concatenation(self) -> bool:
        return self.tokens["+"] and (
            isinstance(self.lhs.type, StringType)
            or isinstance(self.rhs.type, StringType)
        )

    @property
    def type(self):
        if self.is_string_concatenation:
            return StringType()
        else:
            return super().type

    @validate()
    def numeric_operands(self):
        if self.tokens["-"]:
            self.require_numeric_operands("-")
        elif self.tokens["+"]:
            if not self.is_string_concatenation:
                self.require_numeric_operands("+")


class NegateExpr(UnaryOpExpr):
    grammar = [Keyword("-"), lvl8]
    precedence = 7
    type = NumericType()

    @property
    def closure_name(self) -> str:
        return f"blpx_neg_{self.type.glib_type_name}"

    @validate()
    def numeric_operand(self):
        operand = self.children[0]
        if not isinstance(operand.type, NumericType):
            raise CompileError(
                f"Cannot negate non-numeric type {operand.type.full_name}",
                Range(operand.range.start, self.range.end, self.range.original_text),
            )


lvl4 = precedence([AnyOf(NegateExpr, lvl5), ZeroOrMore(AddExpr)])


class CompareExpr(BinaryOpExpr):
    grammar = [
        AnyOf(
            UseExact("op", "=="),
            UseExact("op", "!="),
            UseExact("op", "<"),
            UseExact("op", "<="),
            UseExact("op", ">"),
            UseExact("op", ">="),
        ),
        lvl4,
    ]
    precedence = 3
    type = BoolType()

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(None, must_infer_type=True)

    @property
    def closure_name(self) -> str:
        op = {
            "==": "eq",
            "!=": "ne",
            "<": "lt",
            "<=": "le",
            ">": "gt",
            ">=": "ge",
        }[self.tokens["op"]]

        return f"blpx_{op}_{self.lhs.type.glib_type_name}"


lvl3 = precedence([lvl4, ZeroOrMore(CompareExpr)])


class AndExpr(BinaryOpExpr):
    grammar = [Keyword("&&"), lvl3]
    precedence = 2
    closure_name = "blpx_and"
    type = BoolType()

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(BoolType())


lvl2 = precedence([lvl3, ZeroOrMore(AndExpr)])


class OrExpr(BinaryOpExpr):
    grammar = [Keyword("||"), lvl2]
    precedence = 1
    closure_name = "blpx_or"
    type = BoolType()

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(BoolType())


lvl1 = precedence([lvl2, ZeroOrMore(OrExpr)])


expr.children = [to_parse_node(lvl1)]


@decompiler("lookup", skip_children=True, cdata=True)
def decompile_lookup(
    ctx: DecompileCtx,
    gir: gir.GirContext,
    cdata: str,
    name: str,
    type: T.Optional[str] = None,
):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

    if type is None:
        type = ""
    elif t := ctx.type_by_cname(type):
        type = decompile.full_name(t)
    else:
        type = "$" + type

    assert ctx.current_node is not None

    constant = None
    if len(ctx.current_node.children) == 0:
        constant = cdata
    elif (
        len(ctx.current_node.children) == 1
        and ctx.current_node.children[0].tag == "constant"
    ):
        constant = ctx.current_node.children[0].cdata

    if constant is not None:
        if constant == ctx.template_class:
            ctx.print("template." + name)
        elif constant == "":
            ctx.print(f"item as <{type}>.{name}")
        else:
            ctx.print(constant + "." + name)
        return
    else:
        for child in ctx.current_node.children:
            decompile.decompile_element(ctx, gir, child)

    ctx.print(f" as <{type}>.{name}")


@decompiler("constant", cdata=True)
def decompile_constant(
    ctx: DecompileCtx,
    gir: gir.GirContext,
    cdata: str,
    type: T.Optional[str] = None,
    translatable="false",
    context=None,
    comment=None,
    initial="false",
):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

    gtype = ctx.type_by_cname(type) if type else None

    if truthy(initial) and type is not None:
        if gtype is None:
            ctx.print(f"null as <${type}>")
        else:
            ctx.print(f"null as <{full_name(gtype)}>")
    elif type is None:
        if cdata == ctx.template_class:
            ctx.print("template")
        else:
            ctx.print(cdata)
    elif gtype is None:
        ctx.print(f"{cdata} as <${type}>")
    else:
        _, string = ctx.decompile_value(
            cdata,
            gtype,
            (translatable, context, comment),
        )
        ctx.print(string)


OPERATORS = {
    "blpx_add": "+",
    "blpx_sub": "-",
    "blpx_mul": "*",
    "blpx_div": "/",
    "blpx_mod": "%",
    "blpx_eq": "==",
    "blpx_ne": "!=",
    "blpx_lt": "<",
    "blpx_le": "<=",
    "blpx_gt": ">",
    "blpx_ge": ">=",
    "blpx_and": "&&",
    "blpx_or": "||",
    "blpx_not": "!",
    "blpx_neg": "-",
}


@decompiler("closure", skip_children=True)
def decompile_closure(ctx: DecompileCtx, gir: gir.GirContext, function: str, type: str):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

    op = OPERATORS.get(function)
    if op is not None:
        assert ctx.current_node is not None
        if op == "!" or (op == "-" and len(ctx.current_node.children) == 1):
            ctx.print(op)
        ctx.print("(")
    else:
        if t := ctx.type_by_cname(type):
            type = decompile.full_name(t)
        else:
            type = "$" + type

        ctx.print(f"${function}(")

    assert ctx.current_node is not None
    for i, node in enumerate(ctx.current_node.children):
        decompile_element(ctx, gir, node)

        assert ctx.current_node is not None
        if i < len(ctx.current_node.children) - 1:
            if op is not None:
                ctx.print(f" {op} ")
            else:
                ctx.print(", ")

    if op is None:
        ctx.end_block_with(f") as <{type}>")
    else:
        ctx.end_block_with(")")


@decompiler("try", skip_children=True)
def decompile_try(ctx: DecompileCtx, gir: gir.GirContext):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

    ctx.print("try{")

    assert ctx.current_node is not None
    for i, node in enumerate(ctx.current_node.children):
        decompile_element(ctx, gir, node)

        assert ctx.current_node is not None
        if i < len(ctx.current_node.children) - 1:
            ctx.print(", ")

    ctx.end_block_with("}")
