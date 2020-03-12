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
        'bitarray',
        'conllu',
        'spacy'
    ]
)
