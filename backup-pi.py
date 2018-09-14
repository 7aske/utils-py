
import shutil
from os import listdir, getcwd, remove, walk, devnull
from os.path import join, isdir, isfile, exists
from sys import argv
import sys
import getpass
from subprocess import check_output, call, STDOUT
import re
import atexit


class Backup():
    # drive = '/media/nikola/External Disk'
    # dstDir = None

    src_dir = '/home/nikola/Documents/CODE'
    username = None
    password = None
    address = '192.168.1.12'
    dest = '/home/pi/Documents'
    t_files = 0
    c_files = 0

    def __init__(self):
        if len(argv) == 2:
            self.address == argv[1]

        if len(argv) == 3:
            self.src_dir = self.parse_path(argv[1])
            self.address = argv[2]

        self.username = input('Username:')
        self.password = getpass.unix_getpass('Password:')
        self.t_files = sum([len(files) for r, d, files in walk(self.src_dir)])
        self.backup(self.src_dir)
        call(['/bin/bash', '-i', '-c', 'prune'])

    def backup(self, path):
        FNULL = open(devnull, 'w')
        if path == self.src_dir:

            retval = call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{self.get_root(self.src_dir)}'], stdout=FNULL, stderr=STDOUT)

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

                    r_dir = p[self.get_padding():]

                    retval = call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@{self.address}', f'mkdir -p {self.dest}/{r_dir}'])

                    if retval != 0:
                        raise SystemExit(f'Error creating {r_dir}')
                    self.backup(p)
            elif isfile(p) and not self.ignore(f, p):

                r_file = p[self.get_padding():]
                self.c_files += 1
                self.progress(self.c_files, self.t_files, r_file)

                retval = call(['smbclient', f'//{self.address}/home', '-U', self.username, '--pass', self.password,
                               '-c', f'cd {self.get_root(self.dest)} ; put {p} {r_file}'], stdout=FNULL, stderr=STDOUT)

                if retval != 0:
                    raise SystemExit(f'Error copying {r_file}')
            elif isfile(p) and self.ignore(f, p):
                self.c_files += 1
            else:
                self.c_files += sum([len(files) for r, d, files in walk(p)])

    def progress(self,  count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        sys.stdout.write('\x1b[2K')
        sys.stdout.write('%s\n\r' % (status))
        sys.stdout.write('[%s] %s%s \r' % (bar, percents, '%'))
        sys.stdout.flush()

    def ignore(self, name, path):
        folders = ['node_modules', '__pycache__', '_others', '.vs', '.vscode']
        files = []
        if isdir(path):
            if name in folders:
                return True
        elif isfile(path):
            if name in files:
                return True

        return False

    def get_padding(self):
        return len(self.src_dir) - len(self.get_root(self.src_dir))

    def get_root(self, path):
        return re.findall('[a-zA-Z-_]*$', path)[0]

    def parse_path(self, path):
        if path.startswith('./'):
            return getcwd() + '/' + path[2:]
        elif path.startswith('.'):
            return getcwd()
        return path


@atexit.register
def clear():
    sys.stdout.write('\n')


if __name__ == '__main__':
    backup = Backup()
