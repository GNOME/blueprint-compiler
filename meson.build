project('blueprint-compiler',
  version: '0.20.1',
)

prefix = get_option('prefix')
datadir = join_paths(prefix, get_option('datadir'))

py = import('python').find_installation('python3')

required_python_version = '>=3.9'
if not py.language_version().version_compare(required_python_version)
  error('Python @0@ is required, but found @1@'.format(required_python_version, py.language_version()))
endif

subdir('docs')

configure_file(
  input: 'blueprint-compiler.pc.in',
  output: 'blueprint-compiler.pc',
  configuration: { 'VERSION': meson.project_version() },
  install: not meson.is_subproject(),
  install_dir: join_paths(datadir, 'pkgconfig'),
)

config = configuration_data({
  'VERSION': meson.project_version(),
  'LIBDIR': get_option('prefix') / get_option('libdir'),
  'DATADIR': get_option('prefix') / get_option('datadir'),
  'PYTHON': py.full_path(),
})

if meson.is_subproject()
  config.set('MODULE_PATH', meson.current_source_dir())
else
  config.set('MODULE_PATH', py.get_install_dir())
endif

blueprint_compiler = configure_file(
  input: 'blueprint-compiler-installed.py',
  output: 'blueprint-compiler',
  configuration: config,
  install: not meson.is_subproject(),
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

if meson.is_subproject()
  meson.override_find_program('blueprint-compiler', blueprint_compiler)
else
  install_subdir(
    'blueprintcompiler',
    install_dir: py.get_install_dir(),
    exclude_directories: ['__pycache__'],
  )
endif

subdir('tests')
