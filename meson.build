project('nnlp', ['cpp', 'cython'])

fs = import('fs')
py = import('python').find_installation()

cpp = meson.get_compiler('cpp')
cython = find_program('cython')
prefix = get_option('prefix')

# fst libraries
fst_dep = cpp.find_library('fst', dirs: [prefix / 'lib'])
fstscript_dep = cpp.find_library('fstscript', dirs: [prefix / 'lib'])
fstfar_dep = cpp.find_library('fstfar', dirs: [prefix / 'lib'])
fstfarscript_dep = cpp.find_library('fstfarscript', dirs: [prefix / 'lib'])

# build python module pywrapfst
pywrapfst_dir = 'src' / 'third_party' / 'openfst'
py.extension_module('pywrapfst', pywrapfst_dir / 'pywrapfst.pyx',
  include_directories: [
    include_directories(py.get_path('include')),
    prefix / 'include',
  ],
  install: true,
  install_dir: py.get_path('platlib'),
  cpp_args: ['-std=c++17'],
  dependencies: [fst_dep, fstscript_dep, fstfar_dep, fstfarscript_dep],
  override_options: ['cython_language=cpp'],
)

# build python module fstext
pyfstext_dir = 'src' / 'python3' / 'pyfstext'
pyfstext_cpp = custom_target('pyfstext_cpp',
  input : pyfstext_dir / 'pyfstext.pyx',
  output : 'pyfstext.pyx.cpp',
  command : [cython, '-3', '-I', meson.source_root() / pywrapfst_dir, '@INPUT@', '--cplus', '-o', '@OUTPUT@'],
)
py.extension_module('pyfstext', [
    pyfstext_cpp,
    pyfstext_dir / 'fstrmepslocal.cc',
  ],
  include_directories: [
    include_directories(py.get_path('include')),
    prefix / 'include',
    'src' / 'third_party' / 'kaldi',
    pyfstext_dir
  ],
  install: true,
  install_dir: py.get_path('platlib'),
  cpp_args: ['-std=c++17', '-Wno-sign-compare'],
  dependencies: [fst_dep, fstscript_dep, fstfar_dep, fstfarscript_dep],
  override_options: ['cython_language=cpp'],
)
