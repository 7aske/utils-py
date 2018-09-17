import sys
from os import listdir, getcwd, remove, getcwd
from shutil import rmtree
from os.path import isdir, isfile, join


class Prune():
    path = ''

    def __init__(self):

        if len(sys.argv) == 3:
            if sys.argv[1] == 'code':
                self.path = self.parse_path(f'/home/nikola/Documents/CODE/{sys.argv[2]}')
            if not isdir(self.path):
                raise SystemExit('Invalid path')

        elif len(sys.argv) == 2:
            self.path = self.parse_path(sys.argv[1])
            if not isdir(self.path):
                raise SystemExit('Invalid path')

        elif len(sys.argv) > 3:
            raise SystemExit('Usage: <dir> <sub_dir>')

        else:
            self.path = getcwd()

        print(self.path)
        self.prune(self.path)

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__']
        files = ['git']
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path):
            if name in files:
                return True

        return False

    def parse_path(self, path):
        if path == 'code':
            return '/home/nikola/Documents/CODE'
        elif path.startswith('./'):
            return getcwd() + '/' + path[2:]
        elif path.startswith('.'):
            return getcwd()
        return path

    def prune(self, path):

        for f in listdir(path):
            p = join(path, f)

            if isdir(p):
                if self.ignore(f, p):
                    print(p)
                    rmtree(p)

                else:
                    self.prune(p)

            elif isfile(p):
                if self.ignore(f, p):
                    print(p)
                    remove(p)


if __name__ == '__main__':
    prune = Prune()
