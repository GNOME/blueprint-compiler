# ast_utils.py
#
# Copyright 2021 James Westman <james@jwestman.net>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from .errors import *

class Validator:
    def __init__(self, func, token_name=None, end_token_name=None):
        self.func = func
        self.token_name = token_name
        self.end_token_name = end_token_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        key = "_validation_result_" + self.func.__name__

        if key + "_err" in instance.__dict__:
            # If the validator has failed before, raise a generic Exception.
            # We want anything that depends on this validation result to
            # fail, but not report the exception twice.
            raise AlreadyCaughtError()

        if key not in instance.__dict__:
            try:
                instance.__dict__[key] = self.func(instance)
            except CompileError as e:
                # Mark the validator as already failed so we don't print the
                # same message again
                instance.__dict__[key + "_err"] = True

                # This mess of code sets the error's start and end positions
                # from the tokens passed to the decorator, if they have not
                # already been set
                if self.token_name is not None and e.start is None:
                    group = instance.group.tokens.get(self.token_name)
                    if self.end_token_name is not None and group is None:
                        group = instance.group.tokens[self.end_token_name]
                    e.start = group.start
                if (self.token_name is not None or self.end_token_name is not None) and e.end is None:
                    e.end = instance.group.tokens[self.end_token_name or self.token_name].end

                # Re-raise the exception
                raise e

        # Return the validation result (which other validators, or the code
        # generation phase, might depend on)
        return instance.__dict__[key]


def validate(*args, **kwargs):
    """ Decorator for functions that validate an AST node. Exceptions raised
    during validation are marked with range information from the tokens. Also
    creates a cached property out of the function. """

    def decorator(func):
        return Validator(func, *args, **kwargs)

    return decorator


class Docs:
    def __init__(self, func, token_name=None):
        self.func = func
        self.token_name = token_name


def docs(*args, **kwargs):
    """ Decorator for functions that return documentation for tokens. """

    def decorator(func):
        return Docs(func, *args, **kwargs)

    return decorator
