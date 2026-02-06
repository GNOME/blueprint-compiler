# collect_stats.py
#
# Copyright 2026 James Westman <james@jwestman.net>
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

"""
Collects statistics about property, signal, and child object usage from a sample of blueprint files to help improve
completion suggestions.

Usage:
./blueprint-compiler.py tools collect-stats <path-to-blueprint-regression-tests>
"""

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field

from ..ast_utils import AstNode
from ..language import Child, Object, Property, Signal, Template
from ..parser import parse
from ..tokenizer import tokenize

MAX_ITEMS = 5
MIN_OCCURRENCES = 5


@dataclass
class ClassStats:
    usages: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def summarize(self):
        often_enough = [x for x in self.usages.items() if x[1] >= MIN_OCCURRENCES]
        if len(often_enough) == 0:
            return None

        most_frequent = sorted(often_enough, key=lambda x: x[1], reverse=True)
        return [x[0] for x in most_frequent[:MAX_ITEMS]]


def collect_stats(dir: str):
    class_stats: defaultdict[str, ClassStats] = defaultdict(lambda: ClassStats())

    def walk_ast(ast: AstNode):
        if isinstance(ast, Object) and not isinstance(ast, Template):
            if (
                not ast.class_name.is_extern
                and ast.class_name.gir_type is not None
                and not ast.class_name.gir_type.deprecated
            ):
                class_name = ast.class_name.gir_type.full_name
                class_stat = class_stats[class_name]
                for prop in ast.content.children[Property]:
                    class_stat.usages["p:" + prop.name] += 1
                for signal in ast.content.children[Signal]:
                    class_stat.usages["s:" + signal.full_name] += 1
                for child in ast.content.children[Child]:
                    if not child.object.class_name.is_extern:
                        child_class_name = child.object.class_name.gir_type.full_name
                        class_stat.usages["c:" + child_class_name] += 1

        for child in ast.children:
            walk_ast(child)

    for root, _, files in os.walk(dir):
        for fname in files:
            if not fname.endswith(".blp"):
                continue

            path = os.path.join(root, fname)
            with open(path, "r") as f:
                content = f.read()

            tokens = tokenize(content)
            ast, errors, warnings = parse(tokens)
            if errors is not None or ast is None:
                continue

            walk_ast(ast)

    results = {k: v.summarize() for k, v in class_stats.items()}
    results = {k: v for k, v in results.items() if v is not None}

    with open(os.path.join(os.path.dirname(__file__), "stats.json"), "w") as f:
        json.dump(results, f, indent=2, sort_keys=True)
