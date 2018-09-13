from shutil import copy2
import distutils
from os import mkdir, getcwd, listdir, stat, remove, walk
from sys import argv
import sys
import re
from filecmp import cmp
from os.path import exists, join, normpath, isdir, isfile, getmtime


class Backup():
    src_dir = '/home/nikola/Documents/CODE'
    dest_dir = '/media/nikola/ExternalDisk'
    cpt = 0
    cptc = 0

    def __init__(self):

        if len(argv) == 3:
            self.src_dir = self.parse_path(argv[1])
            self.dest_dir = self.parse_path(argv[2]) + f'/{self.get_root(self.src_dir)}'

        elif len(argv) == 2:
            self.dest_dir = self.parse_path(argv[1]) + f'/{self.get_root(self.src_dir)}'

        else:
            raise SystemExit('Usage: <src> [dest]')
        self.make_dest_dir()
        print(self.src_dir, self.dest_dir)
        self.cpt = sum([len(files) for r, d, files in walk(self.src_dir)])
        self.backup(self.src_dir)

    def parse_path(self, path):
        if path == 'external':
            return '/media/nikola/ExternalDisk'
        elif path == 'code':
            return '/home/nikola/Documents/CODE'
        elif path.startswith('./'):
            return getcwd() + '/' + path[2:]
        elif path.startswith('.'):
            return getcwd()
        return path

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

    def backup(self, path):

        for f in listdir(path):

            s = join(path, f)
            d = self.dest_dir + s[-self.get_padding(s):]
            d_dir = d[len(self.dest_dir) - len(d):]

            if isdir(s) and not self.ignore(f, s):

                if not exists(self.dest_dir + d_dir):
                    mkdir(self.dest_dir + d_dir)
                self.backup(s)

            elif isfile(s) and not self.ignore(f, s):
                self.cptc += 1
                self.progress(self.cptc, self.cpt)
                if not exists(d):
                    try:
                        copy2(s, d)
                        #print(f'Copying {d}')
                    except OSError:
                        SystemExit(f'Error copying {d}')
                else:
                    if not cmp(s, d):
                        if getmtime(s) > getmtime(d):
                            try:
                                remove(d)
                                copy2(s, d)
                                #print(f'Replacing {d}')
                            except OSError:
                                raise SystemExit(f'Error replacing {d}')

    def progress(self,  count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()

    def get_root(self, path):
        return re.findall('[a-zA-Z-_]*$', path)[0]

    def get_padding(self, path):
        return len(path) - len(self.src_dir)

    def make_dest_dir(self):
        if not exists(self.src_dir):
            raise SystemExit('Invalid src directory')

        if not exists(self.parse_path(argv[2])):
            try:
                mkdir(self.parse_path(argv[2]))
            except OSError:
                raise SystemExit('Invalid dest directory')

        if not exists(self.dest_dir):
            try:
                mkdir(self.dest_dir)
            except OSError:
                raise SystemExit('Invalid dest directory')


if __name__ == '__main__':
    backup = Backup()
