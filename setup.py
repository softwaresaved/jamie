from setuptools import setup
import uklaw

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
        'jamie.config',
        'jamie.prediction'],
      install_requires = [
          'pymongo>=3.4.0',
          'pytoml',
          'pandas',
          'numpy>=1.12.0',
          'tqdm',
          'pytest',
          'requests',
          'beautifulsoup4'],
      zip_safe=False)
