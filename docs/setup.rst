=====
Setup
=====

Use Blueprint in your project
-----------------------------

blueprint-compiler works as a meson subproject.

#. Save the following file as ``subprojects/blueprint-compiler.wrap``:

   .. code-block:: cfg

      [wrap-git]
      directory = blueprint-compiler
      url = https://gitlab.gnome.org/jwestman/blueprint-compiler.git
      revision = main
      depth = 1

      [provide]
      program_names = blueprint-compiler

#. Add this to your ``.gitignore``:

   .. code-block::

      /subprojects/blueprint-compiler

#. Add this to the ``meson.build`` file where you build your GResources:

   .. code-block:: meson.build

      blueprints = custom_target('blueprints',
        input: files(
          # LIST YOUR BLUEPRINT FILES HERE
        ),
        output: '.',
        command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
      )

#. In the same ``meson.build`` file, add this argument to your ``gnome.compile_resources`` command:

   .. code-block:: meson.build

      dependencies: blueprints,

#. Convert your .ui XML files to blueprint format. In the future, an automatic
   porting tool is planned.


.. warning::
   The blueprint compiler flattens the directory structure of the resulting XML
   files. You may need to update your ``.gresource.xml`` file to match.
