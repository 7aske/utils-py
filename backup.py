from shutil import copy2
import distutils
from os import mkdir, getcwd, listdir, stat, remove, walk, devnull
from sys import argv
import sys
import re
from filecmp import cmp
from os.path import exists, join, normpath, isdir, isfile, getmtime
import atexit
import getpass
from subprocess import call, check_output, STDOUT, Popen, PIPE


class Backup():
    src_dir = '/home/nikola/Documents/CODE'
    dest_dir = '/media/nikola/ExternalDisk'
    dest = '/home/pi/Documents'
    username = None
    hostname = None
    #password = None
    address = '192.168.1.12'
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

        if not exists(self.src_dir) or not isdir(self.src_dir):
            raise SystemExit('Invalid source dir')
        answer = ''
        possible_answers = ['Y', 'y', 'N', 'n']
        print(f'Source      {self.src_dir} \nDestination {self.dest_dir}')
        while not answer in possible_answers:
            answer = input('Proceed? (Y/N): ')
        if answer == 'y' or answer == 'Y':

            if argv[2] == 'pi' or argv[1] == 'pi':

                self.username = input('Username:')
                ps = Popen(('arp', '-a'), stdout=PIPE)
                output = ps.communicate()[0]
                for line in output.decode().split('\n'):
                    if self.username in line:
                        self.address = re.search(r"([0-9\.]+)", line).group(1)
                self.password = getpass.unix_getpass('Password:')
                self.t_files = sum([len(files) for r, d, files in walk(self.src_dir)])
                self.backup_pi(self.src_dir)

                prune = input('Prune src dir? (Y/N):')

                if prune == 'y' or prune == 'Y':
                    call(['/bin/bash', '-i', '-c', 'prune', self.src_dir])
            else:
                # pass
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

    def backup_pi(self, path):
        FNULL = open(devnull, 'w')
        if path == self.src_dir:

            #retval = call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{self.get_root(self.src_dir)}'], stdout=FNULL, stderr=STDOUT)
            retval = call(['ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{self.get_root(self.src_dir)}'], stdout=FNULL, stderr=STDOUT)

            if retval != 0:
                raise SystemExit('Invalid adress or permission')

        for f in listdir(path):

            p = join(path, f)

            if isdir(p) and not self.ignore(f, p):
                if f == '.git':

                    self.c_files += sum([len(files) for r, d, files in walk(p)])

                    try:
                        out = check_output(['git', '-C', p, 'remote', '-v']).decode()
                        git = re.findall('https://.*github.com/[a-zA-Z0-9]+/[a-zA-Z0-9-_]+', out)[0]
                    except IndexError:
                        raise SystemExit(f'Bad index {p}')
                    try:
                        scr = open(path + '/git', 'w')
                        scr.write(f'git init && git remote add origin && git pull {git}')
                        scr.close()
                    except OSError:
                        raise SystemExit('Cannot write git command file')

                else:

                    r_dir = p[self.get_padding_pi():]

                    #retval = call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{r_dir}'])
                    retval = call(['ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{r_dir}'])

                    if retval != 0:
                        raise SystemExit(f'Error creating {r_dir}')
                    self.backup_pi(p)
            elif isfile(p) and not self.ignore(f, p):

                r_file = p[self.get_padding_pi():]
                self.c_files += 1
                self.progress(self.c_files, self.t_files, r_file)

                # retval = call(['smbclient', f'//{self.address}/home', '-U', self.username, '--pass', self.password,
                #                '-c', f'cd {self.get_root(self.dest)} ; put {p} {r_file}'], stdout=FNULL, stderr=STDOUT)
                retval = call(['scp', p, f'{self.username}@{self.address}:{self.dest}/{r_file}'], stdout=FNULL, stderr=STDOUT)

                if retval != 0:
                    raise SystemExit(f'Error copying {r_file}')
            elif isfile(p) and self.ignore(f, p):
                self.c_files += 1
            else:
                self.c_files += sum([len(files) for r, d, files in walk(p)])

    def parse_path(self, path):
        if path == 'external':
            path = '/media/nikola/ExternalDisk'
        elif path == 'pi':
            path = '/home/pi/Documents'
        elif path == 'dropbox':
            path = '/home/nikola/Dropbox'
        elif path == 'code':
            path = '/home/nikola/Documents/CODE'
        elif path.startswith('./'):
            path = getcwd() + '/' + path[2:]
        elif path.startswith('.'):
            path = getcwd()
        return path

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__', '.vs', '.vscode', '_others']
        files = ['git']
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
        sys.stdout.write('\x1b[2K')
        sys.stdout.write('%s\n\r' % (status))
        sys.stdout.write('[%s] %s%s \r' % (bar, percents, '%'))
        sys.stdout.flush()

    def get_root(self, path):
        return re.findall('[a-zA-Z-_]*$', path)[0]

    def get_padding(self, path):
        return len(self.src_dir) - len(path)

    def get_padding_pi(self):
        return len(self.src_dir) - len(self.get_root(self.src_dir))

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
