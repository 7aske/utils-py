
import atexit
from distutils.dir_util import mkpath
from filecmp import cmp
import getpass
from os.path import exists, join, normpath, isdir, isfile, getmtime
from os import mkdir, getcwd, listdir, stat, remove, walk, devnull
import pysftp as sftp
import re
from shutil import copy2, rmtree
from sys import argv, platform, stdout
from subprocess import call, check_output, STDOUT, Popen, PIPE
from pathlib import Path


class Backup():
    src_dir = str(Path.home()) + '\\Documents\\CODE' if platform == 'win32' else '/home/nik/Documents/CODE'
    dest_dir = 'd:\\ExternalDisk' if platform == 'win32' else '/media/nik/ExternalDisk'
    username = ''
    hostname = ''
    password = ''
    address = '192.168.1.5'
    t_files = 0
    c_files = 0
    slash = '\\' if platform == 'win32' else '/'

    def __init__(self):

        answer = ''
        possible_answers = ['Y', 'y', 'N', 'n']

        if len(argv) == 4:
            if argv[1] == 'code':
                self.src_dir = f'{self.parse_path(argv[1])}{self.slash}{argv[2]}'
                self.dest_dir = f'{self.parse_path(argv[3])}{self.slash}CODE{self.slash}{argv[2]}'
            else:
                raise SystemExit('Invalid path')

        elif len(argv) == 3:
            self.src_dir = self.parse_path(argv[1])
            self.dest_dir = f'{self.parse_path(argv[2])}{self.slash}{self.get_root(self.src_dir)}'

        elif len(argv) == 2:
            self.dest_dir = f'{self.parse_path(argv[1])}{self.slash}{self.get_root(self.src_dir)}'

        else:
            raise SystemExit('Usage: <src> [dest]')
        if not exists(self.src_dir) or not isdir(self.src_dir):
            raise SystemExit('Invalid source dir')

        if 'pi' in argv:
            self.dest_dir = self.dest_dir.replace('\\', '/')

        print(f'Source      {self.src_dir} \nDestination {self.dest_dir}')
        while not answer in possible_answers:
            answer = input('Proceed? (Y/N): ')
        if answer == 'y' or answer == 'Y':

            if 'pi' in argv:
                self.hostname = input('Hostname:')
                self.username = input('Username:')
                self.password = getpass.win_getpass('Password:') if platform == 'win32' else getpass.unix_getpass('Password:')
                self.t_files = sum([len(f) for r, d, f in walk(self.src_dir)])
                self.make_dest_dir_network()
                self.backup_network(self.src_dir)

            else:
                self.make_dest_dir()
                self.t_files = sum([len(f) for r, d, f in walk(self.src_dir)])
                self.backup(self.src_dir)
                self.rm_old(self.dest_dir)
        else:
            SystemExit('Bye!')

    def rm_old(self, path):
        for f in listdir(path):
            s = join(path, f)
            r_dir = ''

            if platform == 'win32':
                r_dir = self.src_dir + s[len(self.dest_dir):]
            else:
                r_dir = self.src_dir + s[len(self.src_dir):]

            if isdir(s):
                if not exists(r_dir):
                    print(r_dir)
                    rmtree(s)
                else:
                    self.rm_old(s)
            elif isfile(s):
                if not exists(r_dir):
                    print(r_dir)
                    remove(s)

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
                self.c_files += sum([len(f) for r, d, f in walk(s)])

    def backup_network(self, path):
        with sftp.Connection(self.hostname, username=self.username, password=self.password) as conn:
            with conn.cd(self.dest_dir):
                for f in listdir(path):
                    s = join(path, f)
                    d = self.dest_dir + s[self.get_padding(s):].replace('\\', '/')
                    r_dir = d[len(self.dest_dir) - len(d):].replace('\\', '/')
                    if isdir(s) and not self.ignore(f, s):
                        if f == '.git':
                            self.c_files += sum([len(f) for r, d, f in walk(s)])
                            try:
                                out = check_output(['git', '-C', s, 'remote', '-v']).decode()
                                git = re.findall('https://.*github.com/[a-zA-Z0-9]+/[a-zA-Z0-9-_]+', out)[0]
                            except IndexError:
                                raise SystemExit(f'Bad index {s}')
                            try:
                                gitp = s[:-4] + 'gitp'
                                scr = open(gitp, 'w')
                                scr.write(f'git init && git remote add origin && git pull {git}')
                                scr.close()
                                conn.put(gitp, remotepath=self.dest_dir+r_dir[:-4]+'/gitp')
                            except OSError:
                                raise SystemExit('Cannot write git command file')
                        else:
                            if not conn.exists(self.dest_dir + r_dir):
                                conn.mkdir(self.dest_dir + r_dir)
                            self.backup_network(s)

                    elif isfile(s) and not self.ignore(f, s):

                        self.c_files += 1
                        self.progress(self.c_files, self.t_files, r_dir)
                        conn.put(s, remotepath=self.dest_dir+r_dir, preserve_mtime=True)

                    elif isfile(s) and self.ignore(f, s):
                        self.c_files += 1
                    else:
                        self.c_files += sum([len(f) for r, d, f in walk(s)])

    def parse_path(self, path):
        if path == 'external':
            path = 'f:\\ExternalDisk' if platform == 'win32' else '/media/nik/ExternalDisk'
        elif path == 'pi':
            path = '/home/pi/Documents'
        elif path == 'dropbox':
            path = str(Path.home()) + '\\Dropbox' if platform == 'win32' else '/home/nik/Dropbox'
        elif path == 'code':
            path = str(Path.home()) + '\\Documents\\CODE' if platform == 'win32' else '/home/nik/Documents/CODE'
        elif path.startswith('./'):
            path = getcwd() + self.slash + path[2:]
        elif path.startswith('.'):
            path = getcwd()
        return path

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__', '.vs', '.vscode', '_others']
        files = ['gitp']
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path) and argv[2] != 'pi' and argv[1] != 'pi':
            if name in files:
                return True

        return False

    def progress(self,  count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        if platform != 'win32':
            stdout.write('\x1b[2K')
        #stdout.write('%s\n\r' % (status))
        stdout.write('[%s] %s%s \r' % (bar, percents, '%'))
        stdout.flush()

    def get_root(self, path):
        return re.findall('[a-zA-Z-_]*$', path)[0]

    def get_padding(self, path):
        return len(self.src_dir) - len(path)

    def get_padding_pi(self):
        return len(self.src_dir) - len(self.get_root(self.src_dir))

    def make_dest_dir_network(self):
        with sftp.Connection(self.hostname, username=self.username, password=self.password) as conn:
            if not conn.exists(self.dest_dir):
                conn.makedirs(self.dest_dir)

    def make_dest_dir(self):
        if not exists(self.src_dir):
            raise SystemExit('Invalid src directory')

        if not exists(self.dest_dir):
            try:
                mkpath(self.dest_dir)
            except OSError:
                raise SystemExit('Invalid dest directory')


@atexit.register
def clear():
    stdout.write('\n')


if __name__ == '__main__':
    backup = Backup()
