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

blueprint_compiler = configure_file(
  input: 'blueprint-compiler.py',
  output: 'blueprint-compiler',
  configuration: {
    'VERSION': meson.project_version(),
  },
  install_dir: get_option('bindir'),
)

# Don't use the output configure_file here--that file is in the build directory
# and won't be able to find the python modules in the source directory.
meson.override_find_program('blueprint-compiler', find_program('blueprint-compiler.py'))

if not meson.is_subproject()
  install_subdir('blueprintcompiler', install_dir: datadir / 'blueprint-compiler')
endif

subdir('tests')
