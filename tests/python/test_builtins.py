# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from konoha_ast import statements, expressions
from konoha_ast.python import parser
import konoha_ast.python.builtins as sa_builtins


class TestPrint:

    def test_print_string(self):
        code = 'print("Hello world")'
        code_block = parser.parse(code)
        assert isinstance(code_block, statements.CodeBlock)
        assert len(code_block.children) == 1
        expr = code_block.children[0]
        assert isinstance(expr, statements.Expr)
        call = expr.value.expression
        assert isinstance(call, sa_builtins.Print)
        assert len(call.objects) == 1  # type: ignore
        literal = call.objects[0].expression  # type: ignore
        assert isinstance(literal, expressions.StrLiteral)
        assert literal.value.expression == "Hello world"

    def test_print_multiple_object(self):
        code = 'print("Hello world", 12, False)'
        code_block = parser.parse(code)
        assert isinstance(code_block, statements.CodeBlock)
        assert len(code_block.children) == 1
        expr = code_block.children[0]
        assert isinstance(expr, statements.Expr)
        call = expr.value.expression
        assert isinstance(call, sa_builtins.Print)
        expression_types = (
            expressions.StrLiteral,
            expressions.IntLiteral,
            expressions.BoolLiteral,
        )
        expression_values = (
            "Hello world",
            12,
            False,
        )
        assert len(call.objects) == len(expression_values)  # type: ignore
        for i, expression in enumerate(call.objects):  # type: ignore
            expression_type = expression_types[i]
            expression_value = expression_values[i]
            assert isinstance(expression.expression, expression_type)
            assert expression.expression.value.expression == expression_value

    def test_print_keyword_only_args(self):
        code = "print(1.2, None, sep='  ', end='', flush=False)"
        code_block = parser.parse(code)
        assert isinstance(code_block, statements.CodeBlock)
        assert len(code_block.children) == 1
        expr = code_block.children[0]
        assert isinstance(expr, statements.Expr)
        call = expr.value.expression
        assert isinstance(call, sa_builtins.Print)
        expression_types = (
            expressions.FloatLiteral,
            expressions.NoneLiteral,
        )
        expression_values = (
            1.2,
            None,
        )
        assert len(call.objects) == len(expression_values)  # type: ignore
        for i, expression in enumerate(call.objects):  # type: ignore
            expression_type = expression_types[i]
            expression_value = expression_values[i]
            assert isinstance(expression.expression, expression_type)
            assert expression.expression.value.expression == expression_value
        assert isinstance(call.sep.expression, expressions.StrLiteral)  # type: ignore
        assert call.sep.expression.value.expression == "  "  # type: ignore
        assert isinstance(call.end.expression, expressions.StrLiteral)  # type: ignore
        assert call.end.expression.value.expression == ""  # type: ignore
        assert isinstance(call.flush.expression, expressions.BoolLiteral)  # type: ignore
        assert call.flush.expression.value.expression is False  # type: ignore
