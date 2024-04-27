# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com


class TempNotSupported(Exception):
    """
    Not Supported Temporarily
    """


class ASTNotSupported(Exception):
    """
    Raised when syntax is not supported
    """


class ConstantNotSupported(Exception):
    """
    Raised when constant is not supported
    """


class VariableContextNotSupported(Exception):
    """
    Raised when variable context is not supported
    """
