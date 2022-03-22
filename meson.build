project('blueprint-compiler',
  version: '0.1.0',
)

subdir('docs')

prefix = get_option('prefix')
datadir = join_paths(prefix, get_option('datadir'))

py = import('python').find_installation('python3')

configure_file(
  input: 'blueprint-compiler.pc.in',
  output: 'blueprint-compiler.pc',
  configuration: { 'VERSION': meson.project_version() },
  install: not meson.is_subproject(),
  install_dir: join_paths(datadir, 'pkgconfig'),
)

install_data(
  'blueprint-compiler.py',
  install_dir: get_option('bindir'),
  rename: 'blueprint-compiler',
)

meson.override_find_program('blueprint-compiler', find_program('blueprint-compiler.py'))

if not meson.is_subproject()
  install_subdir('blueprintcompiler', install_dir: py.get_install_dir())
endif

subdir('tests')
