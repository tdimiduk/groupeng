import subprocess
from shutil import rmtree
from os import remove

version = '1.3'
rname = 'groupeng-{}'.format(version)


subprocess.call(['git', 'clone', 'http://github.com/tdimiduk/groupeng', rname])
def rm(f):
    fname = '{}/{}'.format(rname, f)
    try:
        rmtree(fname)
    except NotADirectoryError:
        remove(fname)

rm('.git')
rm('.gitignore')
rm('tests')
rm('tools')

subprocess.call(['zip', '-r', '{}.zip'.format(rname), rname])
rmtree(rname)


