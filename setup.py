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
        'jamie.data',
        'jamie.prediction'],
      install_requires = [
          'pymongo>=3.4.0',
          'pytoml',  # read .toml configuration files
          'pandas',
          'mysql',
          'mysql-connector-python',
          'nltk',  # text cleaning
          'tabulate', # pretty printing tabular data
          'python-box',  # access dict using dot notation
          'numpy>=1.12.0',
          'tqdm',  # progress bars
          'pytest',
          'requests',
          'beautifulsoup4'],
      zip_safe=False)
