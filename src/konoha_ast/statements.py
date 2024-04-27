# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import collections as _c
from konoha_ast import tree
from konoha_ast import typing as sat


class Statement(tree.IStatement):
    """
    Base class for Statement Node

    This provides some default functionality
    """

    fields: _t.ClassVar[_t.OrderedDict[str, tree.IType]] = _c.OrderedDict()  # All field names and their types

    def __init__(self) -> None:
        super().__init__()
        self.parent = None

    def clone(self, parent: _t.Optional[tree.ICodeBlock] = None) -> tree.IStatement:
        cloned = self.__class__()
        cloned.parent = parent
        for field, field_type in self.fields.items():
            sat.clone_field(cloned, self, field, field_type)
        return cloned

    def post_order(self) -> _t.Iterator[tree.IAST]:
        yield from sat.iterate_sub_ast(self, False)
        yield self

    def pre_order(self) -> _t.Iterator[tree.IAST]:
        yield self
        yield from sat.iterate_sub_ast(self, True)

    def replace(self, new: _t.Union[tree.IStatement, _t.List[tree.IStatement]]) -> None:
        assert self.parent is not None
        assert new is not None
        if not isinstance(new, list):
            new = [new]
        l_children: _t.List[tree.IStatement] = []
        found: bool = False
        for child in self.parent.children:
            if child is self:
                assert not found, (self.parent.children, self, new)
                if new is not None:
                    l_children.extend(new)
                found = True
            else:
                l_children.append(child)
        assert found, (self.parent.children, self, new)
        self.parent.children = l_children
        self.parent.invalidate_sibling_maps()
        for x in new:
            x.parent = self.parent
        self.parent = None

    def remove(self) -> _t.Optional[int]:
        if not self.parent:
            return None
        for i, node in enumerate(self.parent.children):
            if node is not self:
                continue
            del self.parent.children[i]
            self.parent.invalidate_sibling_maps()
            self.parent = None
            return i
        return None

    @property
    def next_sibling(self) -> _t.Optional[tree.IStatement]:
        if self.parent is None:
            return None

        if self.parent.next_sibling_map is None:
            self.parent.update_sibling_maps()
        assert self.parent.next_sibling_map is not None
        return self.parent.next_sibling_map[id(self)]

    @property
    def prev_sibling(self) -> _t.Optional[tree.IStatement]:
        if self.parent is None:
            return None

        if self.parent.prev_sibling_map is None:
            self.parent.update_sibling_maps()
        assert self.parent.prev_sibling_map is not None
        return self.parent.prev_sibling_map[id(self)]


class CodeBlock(tree.ICodeBlock):
    """
    Base class of Code Block

    This provides some default functionality
    """

    fields: _t.ClassVar[_t.OrderedDict[str, tree.IType]] = _c.OrderedDict()  # All field names and their types

    def __init__(self) -> None:
        super().__init__()
        self.parent = None
        self.children = []
        self.prev_sibling_map = {}
        self.next_sibling_map = {}

    def clone(self, parent: _t.Optional[tree.ICodeBlock] = None) -> tree.ICodeBlock:
        cloned = self.__class__()
        cloned.parent = parent
        for field, field_type in self.fields.items():
            sat.clone_field(cloned, self, field, field_type)
        return cloned

    def replace(self, new: tree.IStatement | _t.List[tree.IStatement]) -> None:
        assert self.parent is not None
        assert new is not None
        if not isinstance(new, list):
            new = [new]
        l_children: _t.List[tree.IStatement] = []
        found: bool = False
        for child in self.parent.children:
            if child is self:
                assert not found, (self.parent.children, self, new)
                if new is not None:
                    l_children.extend(new)
                found = True
            else:
                l_children.append(child)
        assert found, (self.children, self, new)
        self.parent.children = l_children
        self.parent.invalidate_sibling_maps()
        for x in new:
            x.parent = self.parent
        self.parent = None

    def remove(self) -> _t.Optional[int]:
        if not self.parent:
            return None
        for i, node in enumerate(self.parent.children):
            if node is not self:
                continue
            del self.parent.children[i]
            self.parent.invalidate_sibling_maps()
            self.parent = None
            return i
        return None

    def invalidate_sibling_maps(self) -> None:
        self.prev_sibling_map = None
        self.next_sibling_map = None

    def update_sibling_maps(self) -> None:
        prev_map: _t.Dict[int, _t.Optional[tree.IStatement]] = {}
        next_map: _t.Dict[int, _t.Optional[tree.IStatement]] = {}
        self.prev_sibling_map = prev_map
        self.next_sibling_map = next_map
        previous: _t.Optional[tree.IAST] = None
        for current in self.children:
            prev_map[id(current)] = previous
            next_map[id(previous)] = current
            previous = current
        if self.children:
            next_map[id(self.children[-1])] = None

    def set_child(self, index: int, child: tree.IStatement) -> None:
        self.children[index].parent = None
        child.parent = self
        self.children[index] = child
        self.invalidate_sibling_maps()

    def insert_child(self, index: int, child: tree.IStatement) -> None:
        child.parent = self
        self.children.insert(index, child)
        self.invalidate_sibling_maps()

    def append_child(self, child: tree.IStatement) -> None:
        child.parent = self
        self.children.append(child)
        self.invalidate_sibling_maps()

    def pre_order(self) -> _t.Iterator[tree.IAST]:
        yield self
        for child in self.children:
            yield from child.pre_order()

    def post_order(self) -> _t.Iterator[tree.IAST]:
        for child in self.children:
            yield from child.pre_order()
        yield self

    @property
    def next_sibling(self) -> _t.Optional[tree.IStatement]:
        if self.parent is None:
            return None

        if self.parent.next_sibling_map is None:
            self.parent.update_sibling_maps()
        assert self.parent.next_sibling_map is not None
        return self.parent.next_sibling_map[id(self)]

    @property
    def prev_sibling(self) -> _t.Optional[tree.IStatement]:
        if self.parent is None:
            return None

        if self.parent.prev_sibling_map is None:
            self.parent.update_sibling_maps()
        assert self.parent.prev_sibling_map is not None
        return self.parent.prev_sibling_map[id(self)]


class Expr(Statement):
    """
    When an expression, such as a function call, appears as a statement by itself with its return value not used
    or stored, it is wrapped in this container. `value` holds one of the other nodes in this section, a Constant, a
    Name, a Lambda, a Yield or YieldFrom node.
    """

    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("value", sat.Object())])

    def __init__(self) -> None:
        super().__init__()
        self.value = sat.ExpressionSlot(sat.Object, self)


class VariableDeclaration(Statement):
    """
    Declare a variable
    """

    id: sat.ExpressionSlot
    type: sat.ExpressionSlot
    fields = _c.OrderedDict([("id", sat.LiteralStr()), ("type", sat.Type())])

    def __init__(self) -> None:
        super().__init__()
        self.id = sat.ExpressionSlot(sat.LiteralStr, self)
        self.id.set_literal_expression("")
        self.type = sat.ExpressionSlot(sat.Type, self)
        object_type = sat.Object()
        self.type.add_expression(object_type)


class VariableDefinition(Statement):
    """
    Define a variable
    """

    id: sat.ExpressionSlot
    type: sat.ExpressionSlot
    value: sat.ExpressionSlot
    fields = _c.OrderedDict([("id", sat.LiteralStr()), ("type", sat.Type()), ("value", sat.Object())])

    def __init__(self) -> None:
        super().__init__()
        self.id = sat.ExpressionSlot(sat.LiteralStr, self)
        self.id.set_literal_expression("")
        self.type = sat.ExpressionSlot(sat.Type, self)
        object_type = sat.Object()
        self.type.add_expression(object_type)
        self.value = sat.ExpressionSlot(sat.Object, self)
        self.type.set_constraint_slot(self.value)
