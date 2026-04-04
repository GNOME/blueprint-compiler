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

if get_option('python_wheel')
  config = configuration_data({
    'VERSION': meson.project_version(),
    'DATADIR': '',
  })
else
  config = configuration_data({
    'VERSION': meson.project_version(),
    'DATADIR': get_option('prefix') / get_option('datadir'),
  })
endif

configure_file(
  input: 'data/config.py.in',
  output: 'config.py',
  configuration: config,
  install: not meson.is_subproject(),
  install_dir: py.get_install_dir() / 'blueprintcompiler',
)

if not get_option('python_wheel')
  # In wheel builds, the wrapper script is specified in pyproject.toml and doesn't need to be generated here.
  blueprint_compiler = configure_file(
    input: 'data/blueprint-compiler.py.in',
    output: 'blueprint-compiler',
    configuration: { 'PYTHON': py.full_path() },
    install: not meson.is_subproject(),
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x',
  )
endif

if meson.is_subproject()
  if get_option('python_wheel')
    error('Building a wheel from a subproject is not supported')
  endif

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
    exclude_directories: [
      '__pycache__',
      'data/__pycache__',
      'language/__pycache__',
      'linter_rules/__pycache__',
      'outputs/__pycache__'
    ],
  )
endif

subdir('tests')
