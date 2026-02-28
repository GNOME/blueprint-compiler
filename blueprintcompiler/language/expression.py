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
        if rhs := self.rhs:
            return rhs.context[ValueTypeCtx]
        else:
            return self.parent.context[ValueTypeCtx]

    @property
    def type(self) -> T.Optional[GirType]:
        raise NotImplementedError()

    @property
    def rhs(self) -> T.Optional["ExprBase"]:
        if isinstance(self.parent, Expression):
            children = list(self.parent.children)
            if children.index(self) + 1 < len(children):
                return children[children.index(self) + 1]
            else:
                return self.parent.rhs
        else:
            return None


class Expression(ExprBase):
    grammar = expr

    @property
    def last(self) -> ExprBase:
        return self.children[-1]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.last.type

    @validate()
    def validate_for_type(self):
        expected_type = self.parent.context[ValueTypeCtx].value_type
        if self.type is not None and expected_type is not None:
            if not self.type.assignable_to(expected_type):
                castable = (
                    " without casting" if self.type.castable_to(expected_type) else ""
                )
                raise CompileWarning(
                    f"Cannot assign {self.type.full_name} to {expected_type.full_name}{castable}"
                )

    @autofix
    def autofix_cast(self):
        expected_type = self.parent.context[ValueTypeCtx].value_type
        if self.type is not None and expected_type is not None:
            if not self.type.assignable_to(expected_type):
                if self.type.castable_to(expected_type):
                    range = Range(
                        self.range.end, self.range.end, self.range.original_text
                    )
                    return TextEdit(range, f" as <{expected_type.full_name}>")


class InfixExpr(ExprBase):
    @property
    def lhs(self):
        children = list(self.parent_by_type(Expression).children)
        return children[children.index(self) - 1]


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
            if not isinstance(self.rhs, CastExpr):
                raise CompileError('"item" must be cast to its object type')

            if not isinstance(self.rhs.rhs, LookupOp):
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


expr.children = [
    AnyOf(TranslatedExpr, TryExpr, ClosureExpr, LiteralExpr, ["(", Expression, ")"]),
    ZeroOrMore(AnyOf(LookupOp, CastExpr)),
]


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

    if truthy(initial) and type is not None:
        t = ctx.type_by_cname(type)
        if t is None:
            ctx.print(f"null as <${type}>")
        else:
            ctx.print(f"null as <{full_name(t)}>")
    elif type is None:
        if cdata == ctx.template_class:
            ctx.print("template")
        else:
            ctx.print(cdata)
    else:
        _, string = ctx.decompile_value(
            cdata,
            ctx.type_by_cname(type),
            (translatable, context, comment),
        )
        ctx.print(string)


@decompiler("closure", skip_children=True)
def decompile_closure(ctx: DecompileCtx, gir: gir.GirContext, function: str, type: str):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

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
            ctx.print(", ")

    ctx.end_block_with(f") as <{type}>")


@decompiler("try", skip_children=True)
def decompile_try(ctx: DecompileCtx, gir: gir.GirContext):
    if ctx.parent_node is not None and ctx.parent_node.tag == "property":
        ctx.print("expr ")

    ctx.print("try(")

    assert ctx.current_node is not None
    for i, node in enumerate(ctx.current_node.children):
        decompile_element(ctx, gir, node)

        assert ctx.current_node is not None
        if i < len(ctx.current_node.children) - 1:
            ctx.print(", ")

    ctx.end_block_with(")")
