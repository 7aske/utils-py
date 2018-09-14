from shutil import copy2
import distutils
from os import mkdir, getcwd, listdir, stat, remove, walk
from sys import argv
import sys
import re
from filecmp import cmp
from os.path import exists, join, normpath, isdir, isfile, getmtime
import atexit


class Backup():
    src_dir = '/home/nikola/Documents/CODE'
    dest_dir = '/media/nikola/ExternalDisk'
    t_files = 0
    c_files = 0

    def __init__(self):
        if len(argv) == 4:
            if argv[1] == 'code':
                self.src_dir = f'{self.parse_path(argv[1])}/{argv[2]}'
                self.dest_dir = self.parse_path(argv[3]) + f'/CODE/{argv[2]}'
            else:
                raise SystemExit('Invalid path')

        elif len(argv) == 3:
            self.src_dir = self.parse_path(argv[1])
            self.dest_dir = self.parse_path(argv[2]) + f'/{self.get_root(self.src_dir)}'

        elif len(argv) == 2:
            self.dest_dir = self.parse_path(argv[1]) + f'/{self.get_root(self.src_dir)}'

        else:
            raise SystemExit('Usage: <src> [dest]')

        print(self.src_dir, self.dest_dir)

        self.make_dest_dir()
        self.t_files = sum([len(files) for r, d, files in walk(self.src_dir)])

        self.backup(self.src_dir)

    def backup(self, path):

        for f in listdir(path):

            s = join(path, f)
            d = self.dest_dir + s[self.get_padding(s):]
            r_dir = d[len(self.dest_dir) - len(d):]

            if isdir(s) and not self.ignore(f, s):

                if not exists(self.dest_dir + r_dir):
                    mkdir(self.dest_dir + r_dir)
                self.backup(s)

            elif isfile(s) and not self.ignore(f, s):

                self.c_files += 1
                self.progress(self.c_files, self.t_files, r_dir)

                if not exists(d):
                    try:
                        copy2(s, d)
                    except OSError:
                        SystemExit(f'Error copying {d}')
                else:
                    if not cmp(s, d):
                        if getmtime(s) > getmtime(d):
                            try:
                                remove(d)
                                copy2(s, d)
                            except OSError:
                                raise SystemExit(f'Error replacing {d}')
            elif isfile(s) and self.ignore(f, s):
                self.c_files += 1
            else:
                self.c_files += sum([len(files) for r, d, files in walk(s)])

    def parse_path(self, path):
        if path == 'external':
            path = '/media/nikola/ExternalDisk'
        elif path == 'code':
            path = '/home/nikola/Documents/CODE'
        elif path.startswith('./'):
            path = getcwd() + '/' + path[2:]
        elif path.startswith('.'):
            path = getcwd()
        if isdir(path):
            return path
        else:
            raise SystemExit('Invalid directory')

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__', '.vs', '.vscode']
        files = ['git']
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path):
            if name in files:
                return True

        return False

    def progress(self,  count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        sys.stdout.write('\x1b[2K')
        sys.stdout.write('%s\n\r' % (status))
        sys.stdout.write('[%s] %s%s \r' % (bar, percents, '%'))
        sys.stdout.flush()

    def get_root(self, path):
        return re.findall('[a-zA-Z-_]*$', path)[0]

    def get_padding(self, path):
        return len(self.src_dir) - len(path)

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


@atexit.register
def clear():
    sys.stdout.write('\n')


if __name__ == '__main__':
    backup = Backup()
