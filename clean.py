from sys import argv, platform
from os import listdir, remove, getcwd
from shutil import rmtree
from os.path import isdir, isfile, join, dirname
from json import load


class Cleaner:
    path = ""
    slash = '\\' if platform == 'win32' else '/'
    settings = {}

    def __init__(self):
        with open(join(dirname(__file__), "settings.json")) as f:
            self.settings = load(f)
        self.path = self.settings[platform]["code"]
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
            raise SystemExit('Usage: <dir> <sub_dir>')

        print('Clean folder ' + self.path)
        answer = ''
        possible_answers = ['Y', 'y', 'N', 'n']

        while answer not in possible_answers:
            answer = input('Proceed? (Y/N): ')

        if answer == 'y' or answer == 'Y':
            self.clean(self.path)

    def clean(self, path):

        for f in listdir(path):
            p = join(path, f)

            if isdir(p):
                if self.ignore(f, p):
                    print(p)
                    rmtree(p)

                else:
                    self.clean(p)

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
            return self.settings[platform][path]
        elif path == 'dropbox':
            return self.settings[platform][path]
        elif path == 'code':
            return self.settings[platform][path]
        elif path == 'remote':
            return self.settings["remote"]["dest"]
        elif path.startswith('./'):
            return join(getcwd(), path[2:])
        elif path.startswith('.'):
            return getcwd()


if __name__ == '__main__':
    cleaner = Cleaner()
