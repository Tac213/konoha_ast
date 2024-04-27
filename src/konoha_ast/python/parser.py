# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import ast
import typing as _t
from konoha_ast import tree
from konoha_ast import statements
from konoha_ast import expressions
from konoha_ast import errors
from konoha_ast.python import ast_extension
import konoha_ast.python.builtins as sa_builtins


class _PyTransformer:
    """
    Transform pyast to konoha ast
    """

    def visit(self, node: ast.AST) -> tree.IAST:
        """
        Visit a node
        """
        ast_name = node.__class__.__name__
        method = f"visit_{ast_name}"
        if not hasattr(self, method):
            raise errors.ASTNotSupported(f"Unsupported ast: {ast_name}, dump:\n{ast.dump(node, indent=4)}\nlineno: {node.lineno}")
        visitor = getattr(self, method)
        return visitor(node)

    def visit_Module(self, node: ast.Module) -> statements.CodeBlock:  # pylint: disable=invalid-name
        code_block = statements.CodeBlock()
        for subnode in node.body:
            sub_konoha_ast = self.visit(subnode)
            assert isinstance(sub_konoha_ast, tree.IStatement)
            code_block.append_child(sub_konoha_ast)
        return code_block

    def visit_Expr(self, node: ast.Expr) -> statements.Expr:  # pylint: disable=invalid-name
        expr = statements.Expr()
        value_konoha_ast = self.visit(node.value)
        assert isinstance(value_konoha_ast, tree.IExpression)
        expr.value.add_expression(value_konoha_ast)
        return expr

    def visit_Constant(self, node: ast.Constant) -> tree.IExpression:  # pylint: disable=invalid-name
        value_type = type(node.value)
        if value_type is bool:
            constant = expressions.BoolLiteral()
        elif value_type is type(None):
            constant = expressions.NoneLiteral()
        elif value_type is int:
            constant = expressions.IntLiteral()
        elif value_type is float:
            constant = expressions.FloatLiteral()
        elif value_type is str:
            constant = expressions.StrLiteral()
        else:
            raise errors.ConstantNotSupported(f"Unsupported constant type: {value_type.__name__}")
        constant.value.set_literal_expression(node.value)
        return constant

    def visit_keyword(self, node: ast.keyword) -> tree.IExpression:
        value_konoha_ast = self.visit(node.value)
        assert isinstance(value_konoha_ast, tree.IExpression)
        return value_konoha_ast

    def visit_Name(self, node: ast.Name) -> tree.IExpression:  # pylint: disable=invalid-name
        context = node.ctx
        if isinstance(context, ast.Load):
            if sa_builtins.is_builtin_expression(node.id):
                expr = sa_builtins.create_builtin_expression(node.id)
            else:
                expr = expressions.VariableLoader()
                expr.id.set_literal_expression(node.id)
        else:
            raise errors.VariableContextNotSupported(f"Unsupported variable context: {context.__class__.__name__}")
        return expr

    def visit_Call(self, node: ast.Call) -> tree.IExpression:  # pylint: disable=invalid-name
        func_konoha_ast = self.visit(node.func)
        if isinstance(func_konoha_ast, expressions.Callable):
            call = func_konoha_ast
        else:
            assert isinstance(func_konoha_ast, expressions.VariableLoader)
            call = expressions.Call()
            call.func.add_expression(func_konoha_ast)
        for arg in node.args:
            arg_konoha_ast = self.visit(arg)
            assert isinstance(arg_konoha_ast, tree.IExpression)
            call.add_argument(arg_konoha_ast)
        for kw in node.keywords:
            arg_konoha_ast = self.visit(kw)
            assert isinstance(arg_konoha_ast, tree.IExpression)
            assert kw.arg is not None
            call.add_keyword_argument(kw.arg, arg_konoha_ast)
        return call

    def visit_AnnAssign(  # pylint: disable=invalid-name
        self, node: ast.AnnAssign
    ) -> _t.Union[statements.VariableDeclaration, statements.VariableDefinition]:
        type_ssast = self.visit(node.annotation)
        assert isinstance(type_ssast, tree.IType)
        if node.value is not None:
            ssast = statements.VariableDefinition()
            ssast.type.remove_expression()
            ssast.type.add_expression(type_ssast)
            value_ssast = self.visit(node.value)
            assert isinstance(value_ssast, tree.IExpression)
            ssast.value.add_expression(value_ssast)
            if ssast.value.expression is None:
                raise TypeError(f"{node.value} is not compatible with {node.annotation}, lineno: {node.lineno}")
        else:
            ssast = statements.VariableDeclaration()
            ssast.type.remove_expression()
            ssast.type.add_expression(type_ssast)
        if isinstance(node.target, ast.Name):
            ssast.id.set_literal_expression(node.target.id)
        else:
            raise errors.TempNotSupported()
        return ssast


def parse(source: _t.Union[str, bytes]) -> tree.IAST:
    """
    Parse python source code to konoha ast
    """
    py_ast = ast_extension.parse(source)
    return _PyTransformer().visit(py_ast)
