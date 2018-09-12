import sys
from os import listdir, getcwd, remove, getcwd
from shutil import rmtree
from os.path import isdir, join


class Prune():

    def __init__(self):

        if len(sys.argv) == 2:

            if sys.argv[1] == 'code':

                self.path = '/home/nikola/Documents/CODE'

            elif isdir(sys.argv[1]):

                self.path = sys.argv[1]

            else:

                raise EnvironmentError('Invalid path')

        elif len(sys.argv) > 2:

            print('Usage: <dir>')

        else:

            self.path = getcwd()

        self.prune(self.path)

    def folder_criteria(self, name):

        my_list = ['node_modules']

        if name in my_list:

            return True

        return False

    def file_criteria(self, name):

        my_list = ['git']

        if name in my_list:

            return True

        return False

    def prune(self, path):

        for f in listdir(path):

            p = join(path, f)

            if isdir(p):

                if self.folder_criteria(f):

                    print(p)
                    rmtree(p)

                else:

                    self.prune(p)

            else:

                if self.file_criteria(f):

                    print(p)
                    remove(p)


if __name__ == '__main__':
    prune = Prune()
