# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    LDESC = open('README.md', 'r').read()
    LDESC = pypandoc.convert(LDESC, 'rst', format='md')
except (ImportError, IOError, RuntimeError) as e:
    print("Could not create long description:")
    print(str(e))
    LDESC = ''

setup(name='brother_ql',
      version = '0.7.1',
      description = 'Python package to talk to Brother QL label printers',
      long_description = LDESC,
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = 'https://github.com/pklaus/brother_ql',
      license = 'GPL',
      packages = ['brother_ql',
                  'brother_ql.backends'],
      entry_points = {
          'console_scripts': [
              'brother_ql_analyse = brother_ql.brother_ql_analyse:main',
              'brother_ql_create  = brother_ql.brother_ql_create:main',
              'brother_ql_print   = brother_ql.brother_ql_print:main',
              'brother_ql_debug   = brother_ql.brother_ql_debug:main',
              'brother_ql_info    = brother_ql.brother_ql_info:main',
          ],
      },
      include_package_data = False,
      zip_safe = True,
      platforms = 'any',
      install_requires = [
          "future",
          "packbits",
          "pillow",
      ],
      extras_require = {
          #'brother_ql_analyse':  ["matplotlib",],
          #'brother_ql_create' :  ["matplotlib",],
      },
      keywords = 'Brother QL-500 QL-570 QL-700 QL-710W QL-720NW',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Visualization',
          'Topic :: System :: Hardware :: Hardware Drivers',
      ]
)



