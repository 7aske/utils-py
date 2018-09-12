import shutil
import os
import sys
import getpass

srcDir = '/home/nikola/Documents/CODE'
drive = '/media/nikola/External Disk'
dstDir = '/media/nikola/External Disk/CODE'


def main():
    if os.path.exists(drive):
        if os.path.exists(dstDir):
            shutil.rmtree(dstDir)
        shutil.copytree(srcDir, dstDir, ignore=ignore_list)


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
