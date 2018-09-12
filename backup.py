import shutil
import os
import sys
import getpass

srcDir = '/home/nikola/Documents/CODE'
drive = '/media/nikola/External Disk'
dstDir = '/media/nikola/External Disk/CODE'


def main():
    username = input('Username:')
    password = getpass.unix_getpass('Password:')
    if os.path.exists(drive):
        if os.path.exists(dstDir):
            shutil.rmtree(dstDir)
        shutil.copytree(srcDir, dstDir, ignore=ignore_list)

    if len(password) > 0 and len(username) > 0:
        os.system(
            f'smbclient //192.168.1.12/home -W WORKGROUP -U {username} --pass {password} -c \'prompt OFF; recurse ON; cd /home/pi/Documents/CODE; lcd /media/nikola/External" "Disk/CODE; mput *\'')


def ignore_patterns(name, path):
    patterns = ['node_modules', '__pycache__']
    if os.path.isdir(path):
        if name in patterns:
            return True
    return False


def ignore_list(path, files):

    filesToIgnore = []

    for fileName in files:
        fullFileName = os.path.join(os.path.normpath(path), fileName)

        if ignore_patterns(fileName, fullFileName):
            filesToIgnore.append(fileName)
        else:
            print(fileName)

    return filesToIgnore


if __name__ == '__main__':
    main()
