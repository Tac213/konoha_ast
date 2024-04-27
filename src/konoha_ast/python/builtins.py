# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import builtins
import typing as _t
import collections as _c
from konoha_ast import tree
from konoha_ast import expressions
from konoha_ast import typing as sat
from konoha_ast.python import unparser


BUILTINS_MAP: _t.Dict[str, type[tree.IExpression]] = {
    "object": sat.Object,
    "bool": sat.Bool,
    "None": expressions.NoneLiteral,
    "int": sat.Int,
    "float": sat.Float,
    "str": sat.Str,
    "list": sat.List,
}

_IGNORE_NAMES = (
    "object",
    "bool",
    "True",
    "False",
    "None",
    "int",
    "float",
    "str",
    "list",
    "_",
    "__build_class__",
    "__debug__",
    "__doc__",
    "__import__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
)


def is_builtin_expression(builtin_name: str) -> bool:
    """
    Check if the `builtin_name` is a supported builtin expression
    """
    return builtin_name in BUILTINS_MAP


def create_builtin_expression(builtin_name: str) -> tree.IExpression:
    """
    Helper function to create builtin expression
    """
    assert builtin_name in BUILTINS_MAP
    return BUILTINS_MAP[builtin_name]()


def _check_builtin_name_valid(builtin_name: str) -> bool:
    if builtin_name in _IGNORE_NAMES:
        return False
    return builtin_name in dir(builtins)


def _python_builtins(builtin_name: str) -> _t.Callable[[type[tree.IExpression]], type[tree.IExpression]]:
    assert _check_builtin_name_valid(builtin_name)

    def real_decorator(cls: type[tree.IExpression]) -> type[tree.IExpression]:
        BUILTINS_MAP[builtin_name] = cls
        return cls

    return real_decorator


@_python_builtins("print")
class Print(expressions.Callable, unparser.IBuiltinExpressionUnparser):
    objects: _t.List[sat.ExpressionSlot]
    sep: sat.ExpressionSlot
    end: sat.ExpressionSlot
    file: sat.ExpressionSlot
    flush: sat.ExpressionSlot

    fields = _c.OrderedDict(
        [
            ("objects", sat.VariadicArg()),
            ("sep", sat.KeywordOnlyArg("sep", True)[sat.Str()]),
            ("end", sat.KeywordOnlyArg("end", True)[sat.Str()]),
            ("file", sat.KeywordOnlyArg("file", True)[sat.Object()]),
            ("flush", sat.KeywordOnlyArg("flush", True)[sat.Bool()]),
        ]
    )

    type = sat.Function()[
        [
            sat.VariadicArg(),
            sat.KeywordOnlyArg("sep", True)[sat.Str()],
            sat.KeywordOnlyArg("end", True)[sat.Str()],
            sat.KeywordOnlyArg("file", True)[sat.Object()],
            sat.KeywordOnlyArg("flush", True)[sat.Bool()],
        ],
        sat.NoneType(),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.objects = []
        self.sep = sat.ExpressionSlot(sat.Str, self)
        self.end = sat.ExpressionSlot(sat.Str, self)
        self.file = sat.ExpressionSlot(sat.Object, self)
        self.flush = sat.ExpressionSlot(sat.Bool, self)

    def unparse(self) -> str:
        args_codes = []
        for obj in self.objects:
            assert isinstance(obj.expression, tree.IExpression)
            args_codes.append(unparser.unparse_expression(obj.expression))
        if isinstance(self.sep.expression, tree.IExpression):
            args_codes.append(f"sep={unparser.unparse_expression(self.sep.expression)}")
        if isinstance(self.end.expression, tree.IExpression):
            args_codes.append(f"end={unparser.unparse_expression(self.end.expression)}")
        if isinstance(self.file.expression, tree.IExpression):
            args_codes.append(f"file={unparser.unparse_expression(self.file.expression)}")
        if isinstance(self.flush.expression, tree.IExpression):
            args_codes.append(f"flush={unparser.unparse_expression(self.flush.expression)}")
        return f"print({', '.join(args_codes)})"
