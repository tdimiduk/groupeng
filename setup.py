import setuptools

with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='GroupEng',
    version='1.3',
    author='Thomas G. Dimiduk',
    author_email='tom@dimiduk.net',
    description='Automatically create equitable groups',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/tdimiduk/groupeng',
    license='GNU Affero General Public License v3.0',
    packages=['GroupEng'],
    install_requires=[''],
)
