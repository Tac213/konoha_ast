# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from konoha_ast import typing as sat
from konoha_ast import statements, expressions
from konoha_ast.python import parser


def test_literals():
    code = """\
True
False
None
12
0.32
"hello python"
"""
    code_block = parser.parse(code)
    assert isinstance(code_block, statements.CodeBlock)
    expr_types = (
        expressions.BoolLiteral,
        expressions.BoolLiteral,
        expressions.NoneLiteral,
        expressions.IntLiteral,
        expressions.FloatLiteral,
        expressions.StrLiteral,
    )
    expr_values = (
        True,
        False,
        None,
        12,
        0.32,
        "hello python",
    )
    assert len(code_block.children) == len(expr_values)
    for i, expr in enumerate(code_block.children):
        assert isinstance(expr, statements.Expr)
        expr_type = expr_types[i]
        expr_value = expr_values[i]
        expr_v = expr.value.expression
        assert isinstance(expr_v, expr_type)
        assert expr_v.value.expression == expr_value


def test_variable_declaration():
    code = """\
one_var: bool
two_var: int = 1"""
    code_block = parser.parse(code)
    assert isinstance(code_block, statements.CodeBlock)
    assert len(code_block.children) == 2
    var_dec = code_block.children[0]
    var_def = code_block.children[1]
    assert isinstance(var_dec, statements.VariableDeclaration)
    assert isinstance(var_def, statements.VariableDefinition)
    assert isinstance(var_dec.type.expression, sat.Bool)
    assert isinstance(var_def.type.expression, sat.Int)
    var_dec_id = var_dec.id.expression
    var_def_id = var_def.id.expression
    assert var_dec_id == "one_var"
    assert var_def_id == "two_var"
    assert isinstance(var_def.value.type, sat.Int)
    assert isinstance(var_def.value.expression, expressions.IntLiteral)
    assert var_def.value.expression.value.expression == 1
