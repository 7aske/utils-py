import shutil
from os import listdir, system
from os.path import join, isdir
import sys
import getpass
import subprocess
import re
username = input('Username:')
password = getpass.unix_getpass('Password:')

srcDir = '/home/nikola/Documents/CODE'
drive = '/media/nikola/External Disk'
dstDir = '/media/nikola/External Disk/CODE'


def main():
    lister(srcDir)


def lister(path):

    for f in listdir(path):
        p = join(path, f)
        if isdir(p) and not ignore_patterns(f, path):
            if f == '.git':
                out = subprocess.check_output(
                    ['git', '-C', p, 'remote', '-v']).decode()
                urls = re.findall(
                    'https://.*github.com/[a-zA-Z0-9]+/[a-zA-Z0-9-_]+', out)
                if len(urls) == 0:
                    print(out)
                print(urls, p)
            else:
                r_dir = p[len(srcDir) - 4:]
                # print(r_dir)
                # system(
                #    f'sshpass -p {password} ssh {username}@192.168.1.12 "mkdir -p /home/pi/Share/{r_dir}"')
                lister(p)
        else:
            r_file = p[len(srcDir) - 4:]
            # system(
            #     f'sshpass -p {password} scp -r {p} {username}@192.168.1.12:/home/pi/Share/{r_file}')
            # system(
            #    f'smbclient //192.168.1.12/home -U {username} --pass {password} -c \'cd Share ; put {p} {r_file}\'')
            # print(r_file)


def ignore_patterns(name, path):

    if isdir(path):
        if name == 'node_modules' or name == '__pycache__' or name == '_others':
            return True
    return False


if __name__ == '__main__':
    main()
