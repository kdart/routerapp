#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2012 Keith Dart <keith@dartworks.biz>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

"""
Extra database types.

"""

__all__ = ["INTEGER", "SMALLINT", "VARCHAR", "CHAR", "TEXT",
    "NUMERIC", "FLOAT", "REAL", "MACADDR", "TIMESTAMP", "TIME", "DATE", "BOOLEAN",
    "ValidationError", "Cidr", "Inet", "JsonText", "PickleText",
    "ValueType", "validate_value_type"]

import sys
import json
import cPickle as pickle

from pycopia.aid import Enums
from pycopia.ipv4 import IPv4

from sqlalchemy.dialects.sqlite import *

from sqlalchemy import types

dumps = pickle.dumps
loads = pickle.loads


class ValidationError(AssertionError):
    pass


class MacAddress(object):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return self._value


# custom column types.

class Cidr(types.MutableType, types.TypeDecorator):
    """Cidr reprsents networks without host part."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return IPv4(value).network.CIDR

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return IPv4(value)

    def copy_value(self, value):
        if value is None:
            return None
        return IPv4(value)


class MACADDR(types.MutableType, types.TypeDecorator):
    """A MAC address."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(MacAddress(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return MacAddress(value)

    def copy_value(self, value):
        if value is None:
            return None
        return MacAddress(value)



class Inet(types.MutableType, types.TypeDecorator):
    """An IPv4 address type. Columns with this type take and receive IPv4
    objects from the database.
    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return IPv4(value).CIDR

    def copy_value(self, value):
        if value is None:
            return None
        return IPv4(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if "/" in value:
            return IPv4(value)
        else:
            return IPv4(value, "255.255.255.255")


class JsonText(types.TypeDecorator):
    """For columns that store a JSON encoded data structure in a TEXT field.
    """
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def process_result_value(self, value, dialect):
        return json.loads(value)


class PickleText(types.TypeDecorator):
    """For columns that store Python objects in a TEXT column.
    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return loads(value.encode("ascii"))


class ValueType(types.TypeDecorator):
    """base types of attribute value types. Usually a value_type column
    name.
    """

    impl = INTEGER
    enumerations = Enums("object", "string", "unicode", "integer", "float", "boolean")

    def process_bind_param(self, value, dialect):
        return  int(value)

    @classmethod
    def process_result_value(cls, value, dialect):
        return cls.enumerations.find(value)

    @classmethod
    def get_choices(cls):
        return cls.enumerations.choices

    @classmethod
    def get_default(cls):
        return cls.enumerations[0]

    @classmethod
    def validate(cls, value):
        return cls.enumerations.find(int(value))


def validate_value_type(value_type, value):
    try:
        return _VALIDATOR_MAP[value_type](value)
    except (ValueError, TypeError) as err:
        raise ValidationError(err)

### attribute base type validation and conversion
def _validate_float(value):
    return float(value)

def _validate_int(value):
    return int(value)

def _validate_boolean(value):
    if isinstance(value, basestring):
        value = value.lower()
        if value in ("on", "1", "true", "t", "y", "yes"):
            return True
        elif value in ("off", "0", "false", "f", "n", "no"):
            return False
        else:
            raise ValidationError("Invalid boolean string: {!r}".format(value))
    else:
        return bool(value)

def _validate_object(value):
    if isinstance(value, basestring):
        try:
            return eval(value, {}, {})
        except:
            ex, val, tb = sys.exc_info()
            del tb
            raise ValidationError("Could not evaluate object: {}: {}".format(ex,__name__, val))
    else:
        return value

def _validate_string(value):
    return str(value)

def _validate_unicode(value):
    return unicode(value)

_VALIDATOR_MAP = {
    0: _validate_object,
    1: _validate_string,
    2: _validate_unicode,
    3: _validate_int,
    4: _validate_float,
    5: _validate_boolean,
}

