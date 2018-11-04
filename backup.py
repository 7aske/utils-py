import atexit
from distutils.dir_util import mkpath
from filecmp import cmp
import getpass
from os.path import exists, isdir, isfile, getmtime, join, dirname, basename
from os import mkdir, getcwd, listdir, remove, walk
import pysftp as sftp
from pysftp import CnOpts
import re
from shutil import copy2, rmtree
from sys import argv, platform, stdout
from subprocess import check_output
from json import load


class Backup:
    src_dir = ''
    dest_dir = ''
    username = ''
    hostname = ''
    password = ''
    t_files = 0
    c_files = 0
    slash = '\\' if platform == 'win32' else '/'
    settings = {}

    def __init__(self):
        try:
            with open(join(dirname(__file__), "settings.json")) as f:
                self.settings = load(f)
        except OSError:
            print("Cannot open settings file")
            self.src_dir = self.parse_path("code")
            self.dest_dir = self.parse_path("external")

        answer = ''
        possible_answers = ['Y', 'y', 'N', 'n']
        if len(argv) == 4:
            self.src_dir = self.parse_path(argv[1])
            self.dest_dir = join(self.parse_path(argv[2]), basename(self.src_dir), argv[3])
        elif len(argv) == 3:
            self.src_dir = self.parse_path(argv[1])
            self.dest_dir = join(self.parse_path(argv[2]), basename(self.src_dir))
        elif len(argv) == 2:
            self.src_dir = self.settings[platform]["code"]
            self.dest_dir = join(self.parse_path(argv[1]), basename(self.src_dir))
        elif len(argv) == 1:
            self.src_dir = self.settings[platform]["code"]
            self.dest_dir = join(self.settings[platform]["external"], basename(self.src_dir))
        else:
            raise SystemExit('Usage: <src> [dest]')

        if not exists(self.src_dir) or not isdir(self.src_dir):
            raise SystemExit('Invalid source dir')

        print(f'Source      {self.src_dir} \nDestination {self.dest_dir}')
        while answer not in possible_answers:
            answer = input('Proceed? (Y/N): ')

        if answer == 'y' or answer == 'Y':

            if 'remote' in argv:
                if len(self.settings["remote"]["hostname"]) == 0:
                    self.hostname = input('Hostname:')
                else:
                    self.hostname = self.settings["remote"]["hostname"]

                if len(self.settings["remote"]["username"]) == 0:
                    self.username = input('Username:')
                else:
                    self.username = self.settings["remote"]["username"]

                self.password = getpass.win_getpass('Password:') if platform == 'win32' else getpass.unix_getpass(
                    'Password:')
                self.t_files = sum([len(f) for r, d, f in walk(self.src_dir)])
                self.make_dest_dir_network()
                self.backup_network(self.src_dir)

            else:
                self.make_dest_dir()
                self.t_files = sum([len(f) for r, d, f in walk(self.src_dir)])
                self.backup(self.src_dir)
                self.rm_old(self.dest_dir)
        else:
            raise SystemExit('Bye!')

    def rm_old(self, path):
        for f in listdir(path):
            s = join(path, f)

            if platform == 'win32':
                r_dir = self.src_dir + s[len(self.dest_dir):]
            else:
                r_dir = self.src_dir + s[len(self.src_dir):]

            if isdir(s):
                if not exists(r_dir):
                    try:
                        print(r_dir)
                        rmtree(s)
                    except WindowsError as e:
                        print("Error deleting: %s" % r_dir)
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
        opts = CnOpts()
        opts.hostkeys = None
        with sftp.Connection(self.hostname, username=self.username, password=self.password, cnopts=opts) as conn:
            with conn.cd(self.dest_dir):
                for f in listdir(path):
                    s = join(path, f)
                    d = self.dest_dir + s[self.get_padding(s):]
                    if self.settings["remote"]["platform"] == "linux":
                        d.replace("\\", "/")
                    r_dir = d[len(self.dest_dir) - len(d):]
                    if self.settings["remote"]["platform"] == "linux":
                        r_dir.replace("\\", "/")
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
                                conn.put(gitp, remotepath=self.dest_dir + r_dir[:-4] + '/gitp')
                            except OSError:
                                raise SystemExit('Cannot write git command file')
                        else:
                            folder = self.dest_dir + r_dir
                            if not conn.exists(folder.replace("\\", "/")):
                                conn.mkdir(folder)
                            self.backup_network(s)

                    elif isfile(s) and not self.ignore(f, s):

                        self.c_files += 1
                        self.progress(self.c_files, self.t_files)
                        conn.put(s, remotepath=self.dest_dir + r_dir, preserve_mtime=True)

                    elif isfile(s) and self.ignore(f, s):
                        self.c_files += 1
                    else:
                        self.c_files += sum([len(f) for r, d, f in walk(s)])

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
            return getcwd() + self.slash + path[2:]
        elif path.startswith('.'):
            return getcwd()

    def ignore(self, name, path):
        folders = self.settings["ignore_folders"]
        files = self.settings["ignore_files"]
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path) and argv[2] != 'pi' and argv[1] != 'pi':
            if name in files:
                return True

        return False

    def progress(self, count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        if platform != 'win32':
            stdout.write('\x1b[2K')
        # stdout.write('%s\n\r' % (status))
        stdout.write('[%s] %s%s \r' % (bar, percents, '%'))
        stdout.flush()

    def get_padding(self, path):
        return len(self.src_dir) - len(path)

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
