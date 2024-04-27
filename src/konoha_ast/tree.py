# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import abc
import typing as _t


class IAST(metaclass=abc.ABCMeta):
    """
    Interface of AST node
    """

    parent: _t.Optional["IAST"]  # Parent node pointer, or None
    fields: _t.ClassVar[_t.OrderedDict[str, "IType"]]  # All field names and their types

    @abc.abstractmethod
    def clone(self, parent: _t.Optional[_t.Union["IAST", "IExpressionSlot"]] = None) -> "IAST":
        """
        Return a cloned (deep) copy of self.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def post_order(self) -> _t.Iterator["IAST"]:
        """
        Return a post-order iterator for the tree.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def pre_order(self) -> _t.Iterator["IAST"]:
        """
        Return a post-order iterator for the tree.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def remove(self) -> _t.Optional[int]:
        """
        Remove the node from the tree. Returns the position of the node in its
        parent's children before it was removed.
        """
        raise NotImplementedError


class IStatement(IAST, metaclass=abc.ABCMeta):
    """
    Interface of statement
    """

    parent: _t.Optional["ICodeBlock"]  # Parent node pointer, or None

    @abc.abstractmethod
    def clone(self, parent: _t.Optional["ICodeBlock"] = None) -> _t.Self:
        """
        Return a cloned (deep) copy of self.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def replace(self, new: _t.Union["IStatement", _t.List["IStatement"]]) -> None:
        """
        Replace this node with a new one in the parent.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def next_sibling(self) -> _t.Optional["IStatement"]:
        """
        The node immediately following the invocant in their parent's children
        list. If the invocant does not have a next sibling, it is None
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def prev_sibling(self) -> _t.Optional["IStatement"]:
        """
        The node immediately preceding the invocant in their parent's children
        list. If the invocant does not have a previous sibling, it is None.
        """
        raise NotImplementedError


class IExpression(IAST, metaclass=abc.ABCMeta):
    """
    Interface of expression
    """

    target_slot: _t.Optional["IExpressionSlot"]  # Target slot of this expression
    type: _t.ClassVar["IType"]  # Value type of this expression

    @property
    @abc.abstractmethod
    def parent(self) -> _t.Optional[IAST]:
        """
        Get parent IAST of expression
        Expressions can only get parent
        """
        raise NotImplementedError

    @abc.abstractmethod
    def clone(self, parent: _t.Optional["IExpressionSlot"] = None) -> _t.Self:
        """
        Return a cloned (deep) copy of self.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def replace(self, new: "IExpression") -> None:
        """
        Replace this node with a new one in the parent.
        """
        raise NotImplementedError


class ICodeBlock(IStatement, metaclass=abc.ABCMeta):
    """
    Interface of code block
    """

    children: _t.List[IStatement]  # List of sub-statements
    prev_sibling_map: _t.Optional[_t.Dict[int, _t.Optional[IStatement]]]
    next_sibling_map: _t.Optional[_t.Dict[int, _t.Optional[IStatement]]]

    @abc.abstractmethod
    def set_child(self, index: int, child: IStatement) -> None:
        """
        Equivalent to `node.children[index] = child`. This method
        also sets the child's parent attribute appropriately.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def insert_child(self, index: int, child: IStatement) -> None:
        """
        Equivalent to `node.children.insert(index, child)`. This method
        also sets the child's parent attribute appropriately.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def append_child(self, child: IStatement) -> None:
        """
        Equivalent to `node.children.append(child)`. This method
        also sets the child's parent attribute appropriately.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def invalidate_sibling_maps(self) -> None:
        """
        Make the sibling maps invalid
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update_sibling_maps(self) -> None:
        """
        Update the sibling maps
        """
        raise NotImplementedError


class IType(IExpression, metaclass=abc.ABCMeta):
    """
    Interface of type
    """

    @abc.abstractmethod
    def is_compatible_with(self, other: "IType") -> bool:
        """
        Returns if the IType is compatible with another IType
        """
        raise NotImplementedError


T = _t.TypeVar("T", bound=IExpression)
S = _t.TypeVar("S", bound=IType)


class IExpressionSlot(_t.Generic[T, S], metaclass=abc.ABCMeta):
    """
    Generic interface of expression slot
    """

    parent: IAST
    type: S

    @property
    @abc.abstractmethod
    def expression(self) -> _t.Union[T, bool, None, int, float, str]:
        """
        Get expression value
        """
        raise NotImplementedError

    @abc.abstractmethod
    def clone(self, parent: IAST) -> _t.Self:
        """
        Return a cloned (deep) copy of self.

        This must be implemented by the concrete subclass.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_occupied(self) -> bool:
        """
        Get whether the slot is occupied
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_compatible_with(self, expr: IExpression) -> bool:
        """
        Returns if the expression is compatible with the slot
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_literal_expression(self, literal: _t.Union[bool, None, int, float, str]) -> None:
        """
        Set literal expression of current slot
        Raise TypeError when type is not literal
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_expression(self, expr: IExpression) -> bool:
        """
        Set expression of current slot
        Raise TypeError when type is literal
        If the slot is not occupied, set successfully and return True
        Else return False
        """
        raise NotImplementedError

    @abc.abstractmethod
    def remove_expression(self) -> bool:
        """
        Remove the expression of current slot
        If the slot is occupied, remove successfully and return True
        Else return False
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_constraint_slot(self, constraint_slot: "IExpressionSlot") -> None:
        """
        Only works if the current slot's type is Type
        It constraints the other slot's type with its expression
        """
        raise NotImplementedError
