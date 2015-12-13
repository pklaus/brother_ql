# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='brother_ql',
      version = '0.6-dev',
      description = 'Python package to talk to Brother QL label printers',
      long_description = '',
      author = 'Philipp Klaus',
      author_email = 'philipp.l.klaus@web.de',
      url = '',
      license = 'GPL',
      packages = ['brother_ql'],
      entry_points = {
          'console_scripts': [
              'brother_ql_read = brother_ql.reader:main',
              'brother_ql_write = brother_ql.create:main',
          ],
      },
      include_package_data = False,
      zip_safe = True,
      platforms = 'any',
      install_requires = ['numpy', 'packbits', 'pillow'],
      extras_require = {
          'brother_ql_read':  ["matplotlib",],
      },
      keywords = 'Brother QL-500 QL-570 QL-710W QL-720NW',
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



