import shutil
from os import listdir, getcwd, remove, system
from os.path import join, isdir
import sys
import getpass
from subprocess import check_output, call
import re


class Backup():
    #drive = '/media/nikola/External Disk'
    #dstDir = None

    srcDir = None
    padding = 0
    username = None
    password = None

    def __init__(self):
        #self.dstDir = self.drive + re.findall('[a-zA-Z-_]*$', self.srcDir)[0]

        self.username = input('Username:')
        self.password = getpass.unix_getpass('Password:')
        self.srcDir = getcwd()
        self.lister(self.srcDir)

    def lister(self, path):
        if path == self.srcDir:

            #system(f'sshpass -p {self.password} ssh {self.username}@192.168.1.12 "mkdir -p /home/pi/Share/{self.get_root()}"')
            call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@192.168.1.12', f'mkdir -p /home/pi/Share/{self.get_root()}'])

        for f in listdir(path):

            p = join(path, f)

            if isdir(p) and not self.ignore_patterns(f, path):

                if f == '.git':

                    out = check_output(
                        ['git', '-C', p, 'remote', '-v']).decode()
                    git = re.findall('https://.*github.com/[a-zA-Z0-9]+/[a-zA-Z0-9-_]+', out)[0]
                    scr = open(path + '/git', 'w')
                    scr.write(f'git init && git remote add origin && git pull {git}')
                    scr.close()

                else:

                    r_dir = p[self.get_padding():]
                    #system(f'sshpass -p {self.password} ssh {self.username}@192.168.1.12 "mkdir -p /home/pi/Share/{r_dir}"')
                    call(['sshpass', '-p', self.password, 'ssh', f'{self.username}@192.168.1.12', f'mkdir -p /home/pi/Share/{r_dir}'])
                    self.lister(p)

            else:

                # system(f'sshpass -p {self.password} scp -r {p} {self.username}@192.168.1.12:/home/pi/Share/{r_file}')
                r_file = p[self.get_padding():]
                #system(f'smbclient //192.168.1.12/home -U {self.username} --pass {self.password} -c \'cd Share ; put {p} {r_file}\'')
                call(['smbclient', '//192.168.1.12/home', '-U', self.username, '--pass', self.password, '-c', f'cd Share ; put {p} {r_file}'])
                if f == 'git':

                    remove(p)

    def ignore_patterns(self, name, path):

        if isdir(path):

            if name == 'node_modules' or name == '__pycache__' or name == '_others':

                return True

        return False

    def get_padding(self):

        return len(self.srcDir) - len(re.findall('[a-zA-Z-_]*$', self.srcDir)[0])

    def get_root(self):

        return re.findall('[a-zA-Z-_]*$', self.srcDir)[0]


if __name__ == '__main__':
    backup = Backup()
