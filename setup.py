from setuptools import setup
import io

# some influences here came from https://github.com/audreyr/cookiecutter/blob/master/setup.py

version = '0.0.3'

with io.open('README.rst', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

setup(
    name     = 'moody',
    version  = version,
    packages = ['moody'],
    license  = 'MIT',
    description = 'A basic CLI to download data from the Mars ODE PDS Node',
    long_description = readme,
    # Author details
    author='Andrew Annex',
    author_email='annex@jhu.edu',
    url='https://github.com/andrewannex/moody',
    download_url='https://github.com/AndrewAnnex/moody/archive/0.0.2.tar.gz',
    install_requires=['requests', 'fire', 'tqdm'],
    entry_points={
        'console_scripts': [
            'moody = moody.moody:main'
        ]
    },

    keywords=['mars', 'nasa', 'ode', 'pds', 'cli', 'tool'],

    classifiers=[
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: GIS'
    ]
)
