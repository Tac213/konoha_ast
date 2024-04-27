# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import black
from konoha_ast.python import parser, unparser


def test_unparse_basic():
    code = """\
print("Hello world")
print(None, False, 13, 34.45)
one_var: bool
two_var: int = 1
print(1.2, None, sep='  ', end='', flush=False)
"""
    sa_code_block = parser.parse(code)
    unparsed_code = unparser.unparse(sa_code_block, need_format=True)
    black.assert_equivalent(code, unparsed_code)
