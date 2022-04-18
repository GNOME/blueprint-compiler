FROM fedora:latest

RUN dnf install -y meson python3-pip gtk4-devel gobject-introspection-devel libadwaita-devel python3-devel
RUN pip3 install furo mypy sphinx coverage

# The version on PyPI is very old and doesn't install. Use the upstream package registry instead.
RUN pip install pythonfuzz --extra-index-url https://gitlab.com/api/v4/projects/19904939/packages/pypi/simple

RUN dnf install -y git
