from setuptools import setup, find_packages
import versioneer

setup(
    name="cxnMiner",
    url='https://github.com/fab-bar/cxnMiner',
    author='Fabian Barteld',
    author_email='fabian.barteld@rub.de',
    license='MIT',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    install_requires=[
        'click',
        'bitarray',
        'conllu<4.0', # with 4.0 pickling TokenList does not work
        'spacy'
    ],
    entry_points={
        'console_scripts': ['cxnminer = cxnminer.cli:main']
    }
)
