# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import collections as _c
from konoha_ast import tree


def check_type_compatibility(type_required: tree.IType, type_provided: tree.IType) -> bool:
    """
    Check if `type_provided` is compatible with `type_required`
    """
    return type_provided.is_compatible_with(type_required)


def clone_field(dest: tree.IAST, src: tree.IAST, field: str, field_type: tree.IType) -> tree.IAST:
    """
    Helper function to clone the `field` with `field_type` from `src` to `dest`
    """
    if isinstance(field_type, (VariadicArg, VariadicKeywordArg)):
        cloned_list = getattr(dest, field)
        assert isinstance(cloned_list, list) and len(cloned_list) == 0
        src_list = getattr(src, field)
        assert isinstance(src_list, list)
        for src_list_item in src_list:
            assert isinstance(src_list_item, tree.IExpressionSlot)
            cloned_list.append(src_list_item.clone(dest))
    else:
        field_slot = getattr(src, field)
        assert isinstance(field_slot, tree.IExpressionSlot)
        cloned_slot = field_slot.clone(dest)
        setattr(dest, field, cloned_slot)
    return dest


def iterate_sub_ast(node: tree.IAST, pre_order: bool) -> _t.Iterator[tree.IAST]:
    """
    Helper function to iterate all sub nodes
    """
    for field, field_type in node.fields.items():
        field_slot = getattr(node, field)
        if isinstance(field_type, (VariadicArg, VariadicKeywordArg)):
            assert isinstance(field_slot, list)
            for item_value in field_slot:
                assert isinstance(item_value, tree.IExpressionSlot)
                if isinstance(item_value.expression, tree.IExpression):
                    if pre_order:
                        yield from item_value.expression.pre_order()
                    else:
                        yield from item_value.expression.post_order()
        else:
            assert isinstance(field_slot, tree.IExpressionSlot)
            if isinstance(field_slot.expression, tree.IExpression):
                if pre_order:
                    yield from field_slot.expression.pre_order()
                else:
                    yield from field_slot.expression.post_order()


T = _t.TypeVar("T", bound=tree.IExpression)
S = _t.TypeVar("S", bound=tree.IType)


class ExpressionSlot(tree.IExpressionSlot[T, S]):

    def __init__(self, type_class: type[S], parent: tree.IAST) -> None:
        super().__init__()
        self.parent = parent
        expr_type = type_class()
        self.type = expr_type
        self._expression: _t.Union[T, bool, None, int, float, str] = None
        self._constraint_slot: _t.Optional[tree.IExpressionSlot] = None

    @property
    def expression(self) -> _t.Union[T, bool, None, int, float, str]:
        return self._expression

    def clone(self, parent: tree.IAST) -> _t.Self:
        expr_type = self.type.__class__
        cloned = self.__class__(expr_type, parent)
        if self.expression is not None:
            if isinstance(self.expression, tree.IExpression):
                expr = self.expression.clone(cloned)
            else:
                expr = self.expression
            self._expression = expr
        return cloned

    @property
    def is_occupied(self) -> bool:
        return self.expression is not None

    def is_compatible_with(self, expr: tree.IExpression) -> bool:
        return check_type_compatibility(self.type, expr.type)

    def set_literal_expression(self, literal: _t.Union[bool, None, int, float, str]) -> None:
        if not isinstance(self.type, LITERAL_TYPES):
            raise TypeError(f"Type of current slot is not literal: {self.type.__class__.__name__}")
        self._expression = literal

    def add_expression(self, expr: tree.IExpression) -> bool:
        if isinstance(self.type, LITERAL_TYPES):
            raise TypeError(f"Type of current slot is literal: {self.type.__class__.__name__}")
        if self.expression is not None:
            return False
        if not check_type_compatibility(self.type, expr.type):
            return False
        expr.target_slot = self
        self._expression = expr  # type: ignore
        self._handle_constraint_slot()
        return True

    def remove_expression(self) -> bool:
        if self.expression is None:
            return False
        assert isinstance(self.expression, tree.IExpression)
        self.expression.target_slot = None
        self._expression = None
        return True

    def set_constraint_slot(self, constraint_slot: tree.IExpressionSlot) -> None:
        assert self.type.__class__ is Type
        assert self._constraint_slot is None
        self._constraint_slot = constraint_slot

    def _handle_constraint_slot(self) -> None:
        if not self._constraint_slot:
            return
        slot = self._constraint_slot
        if self._expression is None:
            return
        assert isinstance(self._expression, Object)
        constraint_type = self._expression.clone()
        slot.type = constraint_type
        if isinstance(slot.expression, tree.IExpression) and not self._constraint_slot.is_compatible_with(slot.expression):
            self._constraint_slot.remove_expression()


def create_expression_slot(node: tree.IAST, type_class: type[tree.IType]) -> ExpressionSlot:
    """
    Helper function to create a expression slot
    """
    return ExpressionSlot(type_class, node)


class Type(tree.IType):
    """
    Base class of types
    """

    fields: _t.ClassVar[_t.OrderedDict[str, tree.IType]] = _c.OrderedDict()  # All field names and their types

    def __init__(self) -> None:
        super().__init__()
        self.target_slot = None

    def clone(self, parent: _t.Optional[tree.IExpressionSlot] = None) -> _t.Self:
        cloned = self.__class__()
        cloned.target_slot = parent
        for field, field_type in self.fields.items():
            clone_field(cloned, self, field, field_type)
        return cloned

    def post_order(self) -> _t.Iterator[tree.IAST]:
        yield from iterate_sub_ast(self, False)
        yield self

    def pre_order(self) -> _t.Iterator[tree.IAST]:
        yield self
        yield from iterate_sub_ast(self, True)

    def replace(self, new: tree.IType) -> None:
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

    def is_compatible_with(self, other: tree.IType) -> bool:
        return self.__class__ is other.__class__


Type.type = Type()


class Object(Type):
    """
    Any type, similar to Python object
    """

    type = Type()

    def is_compatible_with(self, other: tree.IType) -> bool:
        if other.__class__ is Type:
            return False
        return issubclass(self.__class__, other.__class__)


class Bool(Object):
    """
    bool
    """

    type = Type()


class LiteralBool(Bool):
    """
    bool that only allows literal
    """

    type = Type()


class NoneType(Object):
    """
    NoneType
    """

    type = Type()


class LiteralNoneType(NoneType):
    """
    NoneType that only allows literal
    """

    type = Type()


class Int(Object):
    """
    int
    """

    type = Type()


class LiteralInt(Int):
    """
    int that only allows literal
    """


class Float(Object):
    """
    float
    """

    type = Type()


class LiteralFloat(Float):
    """
    float that only allows literal
    """

    type = Type()


class Str(Object):
    """
    str
    """

    type = Type()


class LiteralStr(Str):
    """
    str that only allows literal
    """

    type = Type()


LITERAL_TYPES = (LiteralBool, LiteralNoneType, LiteralInt, LiteralFloat, LiteralStr)


class List(Object):
    """
    list
    """

    item_type: Type

    fields = _c.OrderedDict([("item_type", Type())])
    type = Type()

    def __init__(self) -> None:
        super().__init__()
        self.item_type = Object()

    def clone(self, parent: _t.Optional[tree.IExpressionSlot] = None) -> _t.Self:
        cloned = self.__class__()
        cloned.target_slot = parent
        cloned.item_type = self.item_type.clone()
        return cloned

    def __getitem__(self, param: Type) -> _t.Self:
        self.item_type = param
        return self


class VariadicArg(Type):
    """
    Special type for function arg type with which functions can take a variadic number of arguments
    """

    type = Type()

    def is_compatible_with(self, other: tree.IType) -> bool:
        """
        Handle in callable
        """
        return False


class VariadicKeywordArg(Type):
    """
    Special type for function arg type with which functions can take a variadic number of keyword arguments
    """

    type = Type()

    def is_compatible_with(self, other: tree.IType) -> bool:
        """
        Handle in callable
        """
        return False


class KeywordOnlyArg(Type):
    """
    Special type for keyword only argument to a function call or class definition
    """

    keyword: str
    optional: bool
    arg_type: Type

    fields = _c.OrderedDict([("arg_type", Type())])
    type = Type()

    def __init__(self, keyword: str, optional: bool) -> None:
        super().__init__()
        self.keyword = keyword
        self.optional = optional
        self.arg_type = Object()

    def clone(self, parent: _t.Optional[tree.IExpressionSlot] = None) -> _t.Self:
        cloned = self.__class__(self.keyword, self.optional)
        cloned.target_slot = parent
        cloned.arg_type = self.arg_type.clone()
        return cloned

    def is_compatible_with(self, other: tree.IType) -> bool:
        """
        Handle in callable
        """
        return False

    def __getitem__(self, param: Type) -> _t.Self:
        self.arg_type = param
        return self


class Callable(Object):
    """
    Callable object
    """

    arg_types: _t.List[tree.IType]
    return_type: Type

    fields = _c.OrderedDict([("arg_types", List()[Type()]), ("return_type", Type())])
    type = Type()

    def __init__(self) -> None:
        super().__init__()
        self.arg_types = []
        self.return_type = Object()

    def clone(self, parent: _t.Optional[tree.IExpressionSlot] = None) -> _t.Self:
        cloned = self.__class__()
        cloned.target_slot = parent
        for arg_type in self.arg_types:
            cloned.arg_types.append(arg_type.clone())
        cloned.return_type = self.return_type.clone()
        return cloned

    def __getitem__(self, param: _t.Tuple[_t.Sequence[tree.IType], Type]) -> _t.Self:
        arg_types, return_type = param
        self.arg_types.clear()
        for arg_type in arg_types:
            self.arg_types.append(arg_type)
        self.return_type = return_type
        return self

    def is_compatible_with(self, other: tree.IType) -> bool:  # pylint: disable=too-many-return-statements
        if other.__class__ is Type:
            return False
        if other.__class__ is Object:
            return True
        if isinstance(other, Callable):
            self_arg_index = 0
            other_arg_index = 0
            both_keyword = False
            while self_arg_index < len(self.arg_types):
                self_arg_type = self.arg_types[self_arg_index]
                if other_arg_index >= len(other.arg_types):
                    if isinstance(self_arg_type, VariadicArg):
                        # self expects extra variadic arg
                        # variadic arg's length can be 0, compatible
                        self_arg_index += 1
                        continue
                    if isinstance(self_arg_type, KeywordOnlyArg):
                        # self expects extra keyword only arg
                        if not self_arg_type.optional:
                            # keyword only arg is not optional
                            return False
                        # keyword only arg is optional, compatible
                        self_arg_index += 1
                        continue
                    if isinstance(self_arg_type, VariadicKeywordArg):
                        # self expects extra variadic keyword arg
                        # variadic keyword arg's length can be 0, compatible
                        self_arg_index += 1
                        continue
                    # self expects extra normal arg, incompatible
                    return False
                other_arg_type = other.arg_types[other_arg_index]
                if isinstance(self_arg_type, VariadicArg):
                    if isinstance(other_arg_index, VariadicArg):
                        # both expect variadic arg, compatible
                        self_arg_index += 1
                        other_arg_index += 1
                        continue
                    if isinstance(other_arg_type, KeywordOnlyArg):
                        # other expects keyword only arg whild self expects variadic arg
                        # self may expect keyword only arg later
                        self_arg_index += 1
                        continue
                    if isinstance(other_arg_type, VariadicKeywordArg):
                        # other expects variadic keyword arg whild self expects variadic arg
                        # self may expect keyword arg later
                        self_arg_index += 1
                        continue
                    # other expects noraml arg
                    # compatible with variadic arg
                    other_arg_index += 1
                    continue
                if isinstance(self_arg_type, KeywordOnlyArg):
                    if isinstance(other_arg_type, VariadicArg):
                        # self expects keyword only arg whild other expects variadic arg
                        # other may expect keyword arg later
                        other_arg_index += 1
                        continue
                    if isinstance(other_arg_type, KeywordOnlyArg):
                        # both expect keyword only arg
                        both_keyword = True
                        break
                    if isinstance(other_arg_type, VariadicKeywordArg):
                        # both expect keyword args
                        both_keyword = True
                        break
                    # other expects noraml arg
                    # incompatible with keyword only arg
                    return False
                if isinstance(self_arg_type, VariadicKeywordArg):
                    if isinstance(other_arg_type, VariadicArg):
                        # self expects keyword arg whild other expects variadic arg
                        # other may expect keyword arg later
                        other_arg_index += 1
                        continue
                    if isinstance(other_arg_type, KeywordOnlyArg):
                        # both expect keyword args
                        both_keyword = True
                        break
                    if isinstance(other_arg_type, VariadicKeywordArg):
                        # both expect keyword args
                        both_keyword = True
                        break
                    # other expects noraml arg
                    # incompatible with variadic keyword arg
                    return False
                # self expects normal arg
                if isinstance(other_arg_type, VariadicArg):
                    # self expects normal arg while other expects variadic arg
                    # compatible
                    self_arg_index += 1
                    continue
                if isinstance(other_arg_type, KeywordOnlyArg):
                    # self expects normal arg while other expects keyword only arg
                    # incompatible
                    return False
                if isinstance(other_arg_type, VariadicKeywordArg):
                    # self expects normal arg while other expects keyword args
                    # incompatible
                    return False
                # both expect normal arg
                if not self_arg_type.is_compatible_with(other_arg_type):
                    return False
                self_arg_index += 1
                other_arg_index += 1
            if both_keyword:
                # There are only keyword args left on both sides
                self_all_keyword: _t.Dict[str, Type] = {}
                self_variadic_keyword: bool = False
                while self_arg_index < len(self.arg_types):
                    self_arg_type = self.arg_types[self_arg_index]
                    self_arg_index += 1
                    if isinstance(self_arg_type, VariadicKeywordArg):
                        self_variadic_keyword = True
                        continue
                    assert isinstance(self_arg_type, KeywordOnlyArg)
                    self_all_keyword[self_arg_type.keyword] = self_arg_type.arg_type
                other_required_keyword: _t.Dict[str, Type] = {}
                other_variadic_keyword: bool = False
                while other_arg_index < len(other.arg_types):
                    other_arg_type = other.arg_types[other_arg_index]
                    other_arg_index += 1
                    if isinstance(other_arg_type, VariadicKeywordArg):
                        other_variadic_keyword = True
                        continue
                    assert isinstance(other_arg_type, KeywordOnlyArg)
                    if other_arg_type.optional:
                        continue
                    other_required_keyword[other_arg_type.keyword] = other_arg_type.arg_type
                if other_variadic_keyword:
                    # other may be called with any keywords
                    # which requires self to hav variadic keyword arg
                    if not self_variadic_keyword:
                        # self doesn't meet the requirement
                        # incompatible
                        return False
                for required_keyword, required_arg_type in other_required_keyword.items():
                    if required_keyword not in self_all_keyword:
                        # there is a keyword required by other but doesn't exist in self
                        if self_variadic_keyword:
                            # self has variadic keyword arg
                            # which is compatible with the required keyword
                            continue
                        # self doesn't have variadic keyword arg
                        # incompatible
                        return False
                    self_arg_type = self_all_keyword[required_keyword]
                    if not self_arg_type.is_compatible_with(required_arg_type):
                        # the keyword required by other exists in self
                        # but the type is not compatible
                        return False
            while other_arg_index < len(other.arg_types):
                other_arg_type = other.arg_types[other_arg_index]
                if isinstance(other_arg_type, VariadicArg):
                    # other expects extra variadic arg
                    # other may require a lot more positional arg than self
                    # which is incompatible
                    return False
                if isinstance(other_arg_type, KeywordOnlyArg):
                    # other expects extra keyword only arg
                    if not other_arg_type.optional:
                        # keyword only arg is not optional
                        return False
                    # keyword only arg is optional, compatible
                    other_arg_index += 1
                    continue
                if isinstance(other_arg_type, VariadicKeywordArg):
                    # other expects extra variadic keyword arg
                    # other may require a lot more keyword arg than self
                    # which is incompatible
                    return False
                # other expects extra normal arg, incompatible
                return False
            # now argument type of these two functions are compatible
            if isinstance(other.return_type, NoneType):
                # the other callable object expects the return value to be None
                # it means that it doesn't care about the return value
                # so any return type is compatible
                return True
            return self.return_type.is_compatible_with(other.return_type)
        return False


class Function(Callable):
    """
    Function Objects
    """

    type = Type()
