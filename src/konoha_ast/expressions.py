# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import collections as _c
from konoha_ast import tree
from konoha_ast import typing as sat


class Expression(tree.IExpression):
    """
    Base class of Expression

    This provides some default functionality
    """

    fields: _t.ClassVar[_t.OrderedDict[str, tree.IType]] = _c.OrderedDict()  # All field names and their types
    type: _t.ClassVar[tree.IType] = sat.Object()

    def __init__(self) -> None:
        super().__init__()
        self.target_slot = None

    def clone(self, parent: _t.Optional[tree.IExpressionSlot] = None) -> _t.Self:
        cloned = self.__class__()
        cloned.target_slot = parent
        for field, field_type in self.fields.items():
            sat.clone_field(cloned, self, field, field_type)
        return cloned

    def post_order(self) -> _t.Iterator[tree.IAST]:
        yield from sat.iterate_sub_ast(self, False)
        yield self

    def pre_order(self) -> _t.Iterator[tree.IAST]:
        yield self
        yield from sat.iterate_sub_ast(self, True)

    def replace(self, new: tree.IExpression) -> None:
        slot = self.target_slot
        assert slot is not None
        assert new is not None
        if slot.remove_expression():
            slot.add_expression(new)

    def remove(self) -> _t.Optional[int]:
        if not self.target_slot:
            return
        self.target_slot.remove_expression()

    @property
    def parent(self) -> _t.Optional[tree.IAST]:
        if not self.target_slot:
            return None
        return self.target_slot.parent


class BoolLiteral(Expression):
    """
    A literal bool value. `value` is the value of the literal.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.LiteralBool())])
    type = sat.LiteralBool()

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.LiteralBool, self)
        self.value.set_literal_expression(False)


class NoneLiteral(Expression):
    """
    A literal None value. `value` is always None.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.LiteralNoneType())])
    type = sat.LiteralNoneType()

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.LiteralNoneType, self)
        self.value.set_literal_expression(None)


class IntLiteral(Expression):
    """
    A literal int value. `value` is the value of the literal.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.LiteralInt())])
    type = sat.LiteralInt()

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.LiteralInt, self)
        self.value.set_literal_expression(0)


class FloatLiteral(Expression):
    """
    A literal float value. `value` is the value of the literal.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.LiteralFloat())])
    type = sat.LiteralFloat()

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.LiteralFloat, self)
        self.value.set_literal_expression(0.0)


class StrLiteral(Expression):
    """
    A literal string value. `value` is the value of the literal.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.LiteralStr())])
    type = sat.LiteralStr()

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.LiteralStr, self)
        self.value.set_literal_expression("")


class VariableLoader(Expression):
    """
    A variable loader. `id` holds the name as a string.
    """

    id: sat.ExpressionSlot
    fields = _c.OrderedDict([("id", sat.LiteralStr())])
    type = sat.Object()

    def __init__(self) -> None:
        super().__init__()
        self.id = sat.ExpressionSlot(sat.LiteralStr, self)
        self.id.set_literal_expression("")


class _KeywordType(sat.Type):
    """
    Special type for keyword argument to a function call or class definition
    """

    type = sat.Type()


class Keyword(Expression):
    """
    A keyword argument to a function call or class definition. `arg` is a raw string of the parameter name, `value`
    is a node to pass in.
    """

    arg: sat.ExpressionSlot
    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("arg", sat.LiteralStr()), ("value", sat.Object())])
    type = _KeywordType()

    def __init__(self) -> None:
        super().__init__()
        self.arg = sat.ExpressionSlot(sat.LiteralStr, self)
        self.arg.set_literal_expression("")
        self.value = sat.ExpressionSlot(sat.Object, self)


class Callable(Expression):
    """
    Helper class to create callable expression
    """

    def __init__(self) -> None:
        super().__init__()
        self._positional_field_index = 0
        self._keyword_only_fields: _t.Set[str] = set()
        self._variadic_kwarg_field = ""
        for field, field_type in self.fields.items():
            if isinstance(field_type, sat.KeywordOnlyArg):
                self._keyword_only_fields.add(field)
            elif isinstance(field_type, sat.VariadicKeywordArg):
                self._variadic_kwarg_field = field

    def add_argument(self, argument: tree.IExpression) -> None:
        """
        Add argument expression
        """
        is_set = False
        for field_index, (field, field_type) in enumerate(self.fields.items()):
            if field_index < self._positional_field_index:
                continue
            if isinstance(field_type, sat.VariadicArg):
                field_value = getattr(self, field)
                assert isinstance(field_value, list)
                slot = sat.create_expression_slot(self, sat.Object)
                slot.add_expression(argument)
                field_value.append(slot)
                is_set = True
                break
            slot = getattr(self, field)
            assert isinstance(slot, tree.IExpressionSlot)
            slot.add_expression(argument)
            is_set = True
            self._positional_field_index += 1
            break
        if not is_set:
            raise TypeError(f"Too many positional argument for '{self.__class__.__name__}, argument: {argument}")

    def add_keyword_argument(self, keyword: str, argument: tree.IExpression) -> None:
        """
        Add keyword argument expression
        """
        self._positional_field_index = -1
        if keyword in self._keyword_only_fields:
            slot = getattr(self, keyword)
            assert isinstance(slot, tree.IExpressionSlot)
            # no need to check repeated keyword here, since there may be default value
            slot.add_expression(argument)
            return
        if not self._variadic_kwarg_field:
            raise TypeError(f"'{self.__class__.__name__}' got an unexpected keyword argument: '{keyword}'")
        field_value = getattr(self, self._variadic_kwarg_field)
        assert isinstance(field_value, list)
        for kw in field_value:
            assert isinstance(kw, Keyword)
            if kw.arg.expression == keyword:
                raise SyntaxError(f"'{self.__class__.__name__}' got repeated keyword argument: '{keyword}'")
        kw_ast = Keyword()
        kw_ast.arg.set_literal_expression(keyword)
        kw_ast.value.add_expression(argument)
        slot = self.make_keyword_slot()
        slot.add_expression(kw_ast)
        field_value.append(slot)

    def make_keyword_slot(self) -> tree.IExpressionSlot:
        return sat.ExpressionSlot(_KeywordType, self)


class Call(Callable):
    """
    A function call. `func` is the function, which will often be a Name or Attribute object. Of the arguments:
    - `args` holds a list of the arguments passed by position.
    - `keywords` holds a list of keyword objects representing arguments passed by keyword.
    hen creating a `Call` node, `args` and `keywords` are required, but they can be empty lists.
    """

    func: sat.ExpressionSlot
    args: _t.List[sat.ExpressionSlot]
    keywords: _t.List[sat.ExpressionSlot]
    fields = _t.OrderedDict([("func", sat.Object()), ("args", sat.VariadicArg()), ("keywords", sat.VariadicKeywordArg())])

    def __init__(self) -> None:
        super().__init__()
        self.func = sat.ExpressionSlot(sat.Object, self)
        self.args = []
        self.keywords = []
