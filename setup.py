from setuptools import setup, find_packages

'''
python3 -m unittest
vim setup.py
rm -rf dist/
python3 setup.py sdist bdist_wheel
twine upload --repository pypi dist/*
'''


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(name="kogi",
      version="0.2.3",
      license='MIT',
      author='Kimio Kuramitsu',
      description="Kogi Programming AI",
      url="https://github.com/kkuramitsu/kogi",
      packages=['kogi', 'kogi.liberr',
                'kogi.service', 'kogi.problem', 'kogi.ui'],
      #package_dir={"": "src"},
      package_data={'kogi': ['./*.pegtree', 'ui/*.*', '*/*.txt']},
      install_requires=_requires_from_file('requirements.txt'),
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Framework :: IPython',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Intended Audience :: Education',
      ],
      )
