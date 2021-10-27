if get_option('docs')

sphinx = find_program(['sphinx-build-3', 'sphinx-build'], required: true)

custom_target('docs',
           command: [sphinx, '-b', 'html', '-c', meson.current_source_dir(), meson.current_source_dir(), '@OUTPUT@'],
            output: 'en',
  build_by_default: true
)

endif
