# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import abc
import typing as _t
import itertools
import black
from konoha_ast import tree
from konoha_ast import typing as sat
from konoha_ast import statements as sas
from konoha_ast import expressions as sae

INDENTATION_STR = "    "


class StatementUnparser(_t.Protocol):
    def __call__(self, sa_stmt: tree.IStatement, *, indent: int = 0) -> str: ...


class ExpressionUnparser(_t.Protocol):
    def __call__(self, sa_expr: tree.IExpression) -> str: ...


class IBuiltinExpressionUnparser(metaclass=abc.ABCMeta):
    """
    Interface of builtin expression unparser
    """

    @abc.abstractmethod
    def unparse(self) -> str:
        """
        Unparse this builtin expression to python code
        """
        raise NotImplementedError


_STMT_UNPARSER_MAP: _t.Dict[type[tree.IStatement], StatementUnparser] = {}
_EXPR_UNPARSER_MAP: _t.Dict[type[tree.IExpression], ExpressionUnparser] = {}


def unparse(sa_node: tree.IAST, *, indent: int = 0, need_format: bool = False) -> str:
    """
    Unparse IAST to python code
    """
    if isinstance(sa_node, tree.ICodeBlock):
        return unparse_code_block(sa_node, indent=indent, need_format=need_format)
    if isinstance(sa_node, tree.IStatement):
        return unparse_statement(sa_node, indent=indent, need_format=need_format)
    assert isinstance(sa_node, tree.IExpression)
    return unparse_expression(sa_node, need_format=need_format)


def unparse_statement(sa_stmt: tree.IStatement, *, indent: int = 0, need_format: bool = False) -> str:
    """
    Unparse IStatement to python code
    """
    if isinstance(sa_stmt, tree.ICodeBlock):
        return unparse_code_block(sa_stmt, indent=indent, need_format=need_format)
    unparser = _STMT_UNPARSER_MAP.get(sa_stmt.__class__)
    if not unparser:
        raise NotImplementedError(f"Unsupported statement: {sa_stmt.__class__.__name__}")
    code = unparser(sa_stmt, indent=indent)
    if need_format:
        code = black.format_str(code, mode=black.Mode())
    return code


def unparse_expression(sa_expr: tree.IExpression, *, need_format: bool = False) -> str:
    """
    Unparse IExpression to python code
    """
    if isinstance(sa_expr, IBuiltinExpressionUnparser):
        return sa_expr.unparse()
    unparser = _EXPR_UNPARSER_MAP.get(sa_expr.__class__)
    if not unparser:
        raise NotImplementedError(f"Unsupported expression: {sa_expr.__class__.__name__}")
    code = unparser(sa_expr)
    if need_format:
        code = black.format_str(code, mode=black.Mode())
    return code


def unparse_code_block(sa_code_block: tree.ICodeBlock, *, indent: int = 0, need_format: bool = False) -> str:
    """
    Unparse ICodeBlock to python code
    """
    stmt_codes: _t.List[str] = []
    for sa_stmt in sa_code_block.children:
        stmt_codes.append(unparse_statement(sa_stmt, indent=indent, need_format=False))
    code = "\n".join(stmt_codes)
    if need_format:
        code = black.format_str(code, mode=black.Mode())
    return code


def _stmt_unparser(stmt_class: type[tree.IStatement]) -> _t.Callable[[StatementUnparser], StatementUnparser]:
    def real_decorator(unparser: StatementUnparser) -> StatementUnparser:
        if stmt_class in _STMT_UNPARSER_MAP:
            raise KeyError(f"Duplicated statement unparser: {stmt_class.__name__}")
        _STMT_UNPARSER_MAP[stmt_class] = unparser
        return unparser

    return real_decorator


def _expr_unparser(expr_class: type[tree.IExpression]) -> _t.Callable[[ExpressionUnparser], ExpressionUnparser]:
    def real_decorator(unparser: ExpressionUnparser) -> ExpressionUnparser:
        if expr_class in _EXPR_UNPARSER_MAP:
            raise KeyError(f"Duplicated expression unparser: {expr_class.__name__}")
        _EXPR_UNPARSER_MAP[expr_class] = unparser
        return unparser

    return real_decorator


# ****************************************** Statements Start *********************************************************


@_stmt_unparser(sas.Expr)
def _unparse_expr(sa_stmt: tree.IStatement, *, indent: int = 0) -> str:
    assert isinstance(sa_stmt, sas.Expr)
    assert isinstance(sa_stmt.value.expression, tree.IExpression)
    return f"{INDENTATION_STR * indent}{unparse_expression(sa_stmt.value.expression)}"


@_stmt_unparser(sas.VariableDeclaration)
def _unparse_variable_declaration(sa_stmt: tree.IStatement, *, indent: int = 0) -> str:
    assert isinstance(sa_stmt, sas.VariableDeclaration)
    var_id = sa_stmt.id.expression
    assert isinstance(var_id, str)
    var_type = sa_stmt.type.expression
    assert isinstance(var_type, tree.IExpression)
    return f"{INDENTATION_STR * indent}{var_id}: {unparse_expression(var_type)}"


@_stmt_unparser(sas.VariableDefinition)
def _unparse_variable_definition(sa_stmt: tree.IStatement, *, indent: int = 0) -> str:
    assert isinstance(sa_stmt, sas.VariableDefinition)
    var_id = sa_stmt.id.expression
    assert isinstance(var_id, str)
    var_type = sa_stmt.type.expression
    assert isinstance(var_type, tree.IExpression)
    var_value = sa_stmt.value.expression
    assert isinstance(var_value, tree.IExpression)
    return f"{INDENTATION_STR * indent}{var_id}: {unparse_expression(var_type)} = {unparse_expression(var_value)}"


# ****************************************** Statements Finished ******************************************************

# ****************************************** Expresions Start *********************************************************


@_expr_unparser(sae.BoolLiteral)
def _unparse_bool_literal(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.BoolLiteral)
    assert isinstance(sa_expr.value.expression, bool)
    return f"{sa_expr.value.expression}"


@_expr_unparser(sae.NoneLiteral)
def _unparse_none_literal(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.NoneLiteral)
    return "None"


@_expr_unparser(sae.IntLiteral)
def _unparse_int_literal(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.IntLiteral)
    assert isinstance(sa_expr.value.expression, int)
    return f"{sa_expr.value.expression}"


@_expr_unparser(sae.FloatLiteral)
def _unparse_float_literal(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.FloatLiteral)
    assert isinstance(sa_expr.value.expression, float)
    return f"{sa_expr.value.expression}"


@_expr_unparser(sae.StrLiteral)
def _unparse_str_literal(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.StrLiteral)
    assert isinstance(sa_expr.value.expression, str)
    return f'"{sa_expr.value.expression}"'


@_expr_unparser(sae.VariableLoader)
def _unparse_variable_loader(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.VariableLoader)
    assert isinstance(sa_expr.id.expression, str)
    return f"{sa_expr.id.expression}"


@_expr_unparser(sae.Keyword)
def _unparse_keyword(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.Keyword)
    assert isinstance(sa_expr.arg.expression, str)
    assert isinstance(sa_expr.value.expression, tree.IExpression)
    return f"{sa_expr.arg.expression}={unparse_expression(sa_expr.value.expression)}"


@_expr_unparser(sae.Call)
def _unparse_call(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sae.Call)
    assert isinstance(sa_expr.func.expression, tree.IExpression)
    func_code = unparse_expression(sa_expr.func.expression)
    args_codes = []
    for arg in sa_expr.args:
        assert isinstance(arg.expression, tree.IExpression)
        args_codes.append(unparse_expression(arg.expression))
    kwargs_codes = []
    for kwarg in sa_expr.keywords:
        assert isinstance(kwarg.expression, tree.IExpression)
        kwargs_codes.append(unparse_expression(kwarg.expression))
    return f"{func_code}({', '.join(itertools.chain(args_codes, kwargs_codes))})"


@_expr_unparser(sat.Type)
def _unparse_type_type(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Type)
    return "type"


@_expr_unparser(sat.Object)
def _unparse_type_object(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Object)
    return "object"


@_expr_unparser(sat.Bool)
def _unparse_type_bool(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Bool)
    return "bool"


@_expr_unparser(sat.LiteralBool)
def _unparse_type_literal_bool(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.LiteralBool)
    return "bool"


@_expr_unparser(sat.NoneType)
def _unparse_type_none_type(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.NoneType)
    return "type(None)"


@_expr_unparser(sat.LiteralNoneType)
def _unparse_type_literal_none_type(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.LiteralNoneType)
    return "type(None)"


@_expr_unparser(sat.Int)
def _unparse_type_int(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Int)
    return "int"


@_expr_unparser(sat.LiteralInt)
def _unparse_type_literal_int(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.LiteralInt)
    return "int"


@_expr_unparser(sat.Float)
def _unparse_type_float(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Float)
    return "float"


@_expr_unparser(sat.LiteralFloat)
def _unparse_type_literal_float(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.LiteralFloat)
    return "float"


@_expr_unparser(sat.Str)
def _unparse_type_str(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.Str)
    return "str"


@_expr_unparser(sat.LiteralStr)
def _unparse_type_literal_str(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.LiteralStr)
    return "str"


@_expr_unparser(sat.List)
def _unparse_type_list(sa_expr: tree.IExpression) -> str:
    assert isinstance(sa_expr, sat.List)
    return f"list[{unparse_expression(sa_expr.item_type)}]"


# ****************************************** Expresions Finished ******************************************************
