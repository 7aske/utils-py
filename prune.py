import sys
from os import listdir, getcwd
from shutil import rmtree
from os.path import isdir, join
mypath = '/home/nikola/Documents/CODE'


def criteria(name):
    my_list = ['node_modules']
    if name in my_list:
        return True
    return False


def prune(path):
    for f in listdir(path):
        p = join(path, f)
        if isdir(p):
            if criteria(f):
                print(p)
                rmtree(p)
            else:
                prune(p)


if sys.argv[1]:
    print(sys.argv[1])
    if sys.argv[1] == '.':
        prune(getcwd())
    else:
        prune(join(getcwd(), sys.argv[1]))
else:
    prune(mypath)
