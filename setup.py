from setuptools import setup

setup(name='jamie',
      version='0.1',
      description='Jobs analysis using Machine Information Extraction',
      url='https://github.com/softwaresaved/jobs-analysis',
      author='',
      author_email='hello@example.com',
      scripts=['bin/jamie'],
      packages=[
          'jamie',
          'jamie.analysis',
          'jamie.common',
          'jamie.scrape',
          'jamie.config',
          'jamie.features',
          'jamie.data',
          'jamie.prediction'],
      install_requires=[
          'chevron',  # mustache templating
          'matplotlib',
          'pymongo>=3.4.0',
          'pytoml',  # read .toml configuration files
          'fire',  # command line interface
          'pandas==1.0.3',
          'gitpython==3.1.2',
          'scikit-learn==0.22.2',
          'imbalanced-learn==0.6.2',
          'nltk==3.5',  # text cleaning
          'tabulate',  # pretty printing tabular data
          'python-box==4.2.3',  # access dict using dot notation
          'numpy>=1.12.0',
          'python-slugify',
          'tqdm',  # progress bars
          'pytest',
          'requests==2.22.0',
          'python-slugify',
          'beautifulsoup4==4.9.0'],
      extras_require={
          'docs': ['sphinx'],
          'dev': ['pre-commit', 'black', 'flake8', 'pytest']
      },
      package_data={'jamie': ['data/uk_uni*']},
      zip_safe=False)
