project('gtk-blueprint-tool',
  version: '0.1.0',
)

prefix = get_option('prefix')
libdir = join_paths(prefix, get_option('libdir'))

py = import('python').find_installation('python3')

configure_file(
  input: 'gtk-blueprint-tool.pc.in',
  output: 'gtk-blueprint-tool.pc',
  configuration: { 'VERSION': meson.project_version() },
  install: not meson.is_subproject(),
  install_dir: join_paths(libdir, 'pkgconfig'),
)

meson.override_find_program('gtk-blueprint-tool', find_program('gtk-blueprint-tool.py'))

if not meson.is_subproject()
  install_subdir('gtkblueprinttool', install_dir: py.get_install_dir())
endif

test('tests', py, args: ['-m', 'unittest'])
