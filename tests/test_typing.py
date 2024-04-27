# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

from konoha_ast import typing as sat


class TestTypeCompatibility:

    def test_instance_types(self):
        object_type = sat.Object()
        bool_type = sat.Bool()
        none_type = sat.NoneType()
        int_type = sat.Int()
        float_type = sat.Float()
        str_type = sat.Str()
        assert bool_type.is_compatible_with(object_type)
        assert none_type.is_compatible_with(object_type)
        assert int_type.is_compatible_with(object_type)
        assert float_type.is_compatible_with(object_type)
        assert str_type.is_compatible_with(object_type)
        assert not bool_type.is_compatible_with(none_type)
        assert not int_type.is_compatible_with(float_type)
        assert not none_type.is_compatible_with(float_type)

    def test_class_types(self):
        type_type = sat.Type()
        assert type_type.type.is_compatible_with(type_type)  # type of type is also type
        object_type = sat.Object()
        bool_type = sat.Bool()
        none_type = sat.NoneType()
        int_type = sat.Int()
        float_type = sat.Float()
        str_type = sat.Str()
        assert not object_type.is_compatible_with(type_type)  # when object is treated as a type, it's incompatible with type
        assert object_type.type.is_compatible_with(type_type)  # when object is treated as an expression, it's compatible with type
        assert not bool_type.is_compatible_with(type_type)
        assert bool_type.type.is_compatible_with(type_type)
        assert not none_type.is_compatible_with(type_type)
        assert none_type.type.is_compatible_with(type_type)
        assert not int_type.is_compatible_with(type_type)
        assert int_type.type.is_compatible_with(type_type)
        assert not float_type.is_compatible_with(type_type)
        assert float_type.type.is_compatible_with(type_type)
        assert not str_type.is_compatible_with(type_type)
        assert str_type.type.is_compatible_with(type_type)


class TestCallableCompatibility:

    def test_positional_arg(self):
        callable1 = sat.Callable()[[sat.Str()], sat.NoneType()]
        assert callable1.is_compatible_with(callable1)
        callable2 = sat.Callable()[[sat.Object()], sat.NoneType()]
        assert callable1.is_compatible_with(callable2)
        assert not callable2.is_compatible_with(callable1)
        callable3 = sat.Callable()[[sat.Str(), sat.Int()], sat.Float()]
        assert not callable3.is_compatible_with(callable1)
        assert not callable1.is_compatible_with(callable3)
        callable4 = sat.Callable()[[sat.Str(), sat.Object()], sat.Float()]
        assert callable3.is_compatible_with(callable4)
        assert not callable4.is_compatible_with(callable3)
        callable5 = sat.Callable()[[sat.VariadicArg()], sat.NoneType()]
        assert not callable1.is_compatible_with(callable5)  # no *args in callable1, incompatible
        assert not callable2.is_compatible_with(callable5)
        assert not callable3.is_compatible_with(callable5)
        assert not callable4.is_compatible_with(callable5)
        callable6 = sat.Callable()[[sat.Bool(), sat.VariadicArg()], sat.NoneType()]
        assert callable6.is_compatible_with(callable5)

    def test_void_callable(self):
        callable_provided = sat.Callable()[[], sat.Bool()]
        callable_required = sat.Callable()[[], sat.NoneType()]
        assert callable_provided.is_compatible_with(callable_required)

    def test_keyword_arg(self):
        callable1 = sat.Callable()[[sat.Int(), sat.KeywordOnlyArg("a", True)], sat.NoneType()]
        callable2 = sat.Callable()[[sat.Int(), sat.KeywordOnlyArg("a", False), sat.KeywordOnlyArg("b", True)], sat.NoneType()]
        callable3 = sat.Callable()[
            [sat.VariadicArg(), sat.KeywordOnlyArg("a", False), sat.KeywordOnlyArg("b", True), sat.KeywordOnlyArg("c", False)],
            sat.NoneType(),
        ]
        assert callable1.is_compatible_with(callable2)
        assert not callable1.is_compatible_with(callable3)  # keyword c is required
        callable4 = sat.Callable()[[sat.VariadicArg(), sat.KeywordOnlyArg("a", False), sat.VariadicKeywordArg()], sat.NoneType()]
        assert not callable1.is_compatible_with(callable4)  # no **kwargs in callable1, incompatible
        callable5 = sat.Callable()[[sat.VariadicArg(), sat.VariadicKeywordArg()], sat.NoneType()]
        assert callable4.is_compatible_with(callable5)
        assert callable5.is_compatible_with(callable4)
