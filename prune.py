from sys import argv, platform
from os import listdir, getcwd, remove, getcwd
from shutil import rmtree
from os.path import isdir, isfile, join


class Prune():
    path = 'd:\\Users\\nik\\Documents\\CODE\\' if platform == 'win32' else '/home/nikola/Documents/CODE/'
    slash = '\\' if platform == 'win32' else '/'

    def __init__(self):
        if len(argv) == 3:
            if argv[1] == 'code':
                self.path = self.parse_path(argv[1]) + self.slash + argv[2]
            if not isdir(self.path):
                raise SystemExit('Invalid path')

        elif len(argv) == 2:
            self.path = self.parse_path(argv[1])
            if not isdir(self.path):
                raise SystemExit('Invalid path')

        elif len(argv) > 3:
            raise SystemExit('Usage: <dir> <sub_dir>')

        else:
            self.path = getcwd()

        print('Pruning folder ' + self.path)
        self.prune(self.path)

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

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__']
        files = ['gitp']
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path):
            if name in files:
                return True

        return False

    def parse_path(self, path):
        if path == 'external':
            path = 'f:\\ExternalDisk' if platform == 'win32' else '/media/nik/ExternalDisk'
        elif path == 'pi':
            path = '/home/pi/Documents'
        elif path == 'dropbox':
            path = 'd:\\Users\\nik\\Dropbox' if platform == 'win32' else '/home/nik/Dropbox'
        elif path == 'code':
            path = 'd:\\Users\\nik\\Documents\\CODE' if platform == 'win32' else '/home/nik/Documents/CODE'
        elif path.startswith('./'):
            path = getcwd() + self.slash + path[2:]
        elif path.startswith('.'):
            path = getcwd()
        return path


if __name__ == '__main__':
    prune = Prune()
