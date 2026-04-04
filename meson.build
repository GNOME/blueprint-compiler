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
  input: 'data/blueprint-compiler-installed.py.in',
  output: 'blueprint-compiler',
  configuration: config,
  install: not meson.is_subproject(),
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

if meson.is_subproject()
  meson.override_find_program('blueprint-compiler', blueprint_compiler)
else
  if get_option('python_wheel')
    pkgconfig_path = 'share' / 'pkgconfig'
  else
    pkgconfig_path = 'pkgconfig'
  endif

  blueprint_compiler_pc = configure_file(
    input: 'data/blueprint-compiler.pc.in',
    output: 'blueprint-compiler.pc',
    configuration: { 'VERSION': meson.project_version() },
    install_dir: get_option('datadir') / pkgconfig_path,
  )

  install_subdir(
    'blueprintcompiler',
    install_dir: py.get_install_dir(),
    exclude_directories: ['__pycache__'],
  )
endif

subdir('tests')
