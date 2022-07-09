Overview
========

Blueprint is a markup language and compiler for GTK 4 user interfaces.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   setup
   translations
   flatpak
   examples
   packaging


.. code-block::

   using Gtk 4.0;

   template MyAppWindow : ApplicationWindow {
     default-width: 600;
     default-height: 300;
     title: _("Hello, Blueprint!");

     [titlebar]
     HeaderBar {}

     Label {
       label: bind MyAppWindow.main_text;
     }
   }

Blueprint helps you build user interfaces in GTK quickly and declaratively.
It has modern IDE features like code completion and hover documentation, and
the compiler points out mistakes early on so you can focus on making your app
look amazing.

Features
--------

- **Easy setup.** A porting tool is available to help port your projects from
  XML. The compiler's only dependency is Python, and it can be included as
  a meson subproject. :doc:`See the Setup page for more information. <setup>`
- **Concise syntax.** No more clumsy XML! Blueprint is designed from the ground
  up to match GTK's widget model, including templates, child types, signal
  handlers, and menus.
- **Easy to learn.** The syntax should be very familiar to most people. Scroll
  through the :doc:`examples page <examples>` for a quick overview of the whole
  language.
- **Modern tooling.** IDE integration for `GNOME Builder <https://developer.gnome.org/documentation/introduction/builder.html>`_
  is in progress, and a VS Code extension is also planned.

Links
-----

- `Source code <https://gitlab.gnome.org/jwestman/blueprint-compiler>`_
- `Vim syntax highlighting plugin by thetek42 <https://github.com/thetek42/vim-blueprint-syntax>`_
- `Vim syntax highlighting plugin by gabmus <https://gitlab.com/gabmus/vim-blueprint>`_
- `GNU Emacs major mode by DrBluefall <https://github.com/DrBluefall/blueprint-mode>`_
- `Visual Studio Code plugin by bodil <https://github.com/bodil/vscode-blueprint>`_

Built with Blueprint
--------------------

- `Dialect <https://github.com/dialect-app/dialect>`_
- `Extension Manager <https://github.com/mjakeman/extension-manager>`_
- `favagtk <https://gitlab.gnome.org/johannesjh/favagtk>`_
- `Feeds <https://gitlab.gnome.org/World/gfeeds>`_
- `Geopard <https://github.com/ranfdev/Geopard>`_
- `Giara <https://gitlab.gnome.org/World/giara>`_
- `Health <https://gitlab.gnome.org/World/Health>`_
- `HydraPaper <https://gitlab.com/gabmus/HydraPaper>`_
- `Identity <https://gitlab.gnome.org/YaLTeR/identity>`_
- `Login Manager Settings <https://github.com/realmazharhussain/gdm-settings>`_
- `Paper <https://gitlab.com/posidon_software/paper>`_
- `Passes <https://github.com/pablo-s/passes>`_
- `Plitki <https://github.com/YaLTeR/plitki>`_
- `Solanum <https://gitlab.gnome.org/World/Solanum>`_
- `Swatch <https://gitlab.gnome.org/GabMus/swatch>`_
- `Text Pieces <https://github.com/liferooter/textpieces>`_
- `Video Trimmer <https://gitlab.gnome.org/YaLTeR/video-trimmer>`_
- `WhatIP <https://gitlab.gnome.org/GabMus/whatip>`_
- `Workbench <https://github.com/sonnyp/Workbench>`_
