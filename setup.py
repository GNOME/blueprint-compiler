# SPDX-FileCopyrightText: 2021 GNOME Foundation
# SPDX-License-Identifier: Apache-2.0 OR GPL-3.0-or-later

# Adapted from the gi-docgen source code by James Westman <james@jwestman.net>

import sys

from gtkblueprinttool import main

from distutils.command.build_py import build_py as _build_py
from setuptools import setup


class BuildCommand(_build_py):

    def generate_pkgconfig_file(self):
        lines = []
        with open('gtk-blueprint-tool.pc.in', 'r') as f:
            for line in f.readlines():
                new_line = line.strip().replace('@VERSION@', main.VERSION)
                lines.append(new_line)
        with open('gtk-blueprint-tool.pc', 'w') as f:
            f.write('\n'.join(lines))

    def run(self):
        self.generate_pkgconfig_file()
        return super().run()


def readme_md():
    '''Return the contents of the README.md file'''
    return open('README.md').read()


entries = {
    'console_scripts': ['gtk-blueprint-tool=gtkblueprinttool.main:main'],
}

packages = [
    'gtkblueprinttool',
]

data_files = [
    ('share/pkgconfig', ['gtk-blueprint-tool.pc']),
]

if __name__ == '__main__':
    setup(
        cmdclass={
            'build_py': BuildCommand,
        },
        name='gtk-blueprint-tool',
        version=main.VERSION,
        license='GPL-3.0-or-later',
        long_description=readme_md(),
        long_description_content_type='text/markdown',
        include_package_data=True,
        packages=packages,
        entry_points=entries,
        data_files=data_files,
    )
