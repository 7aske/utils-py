import shutil
from os import mkdir
import sys
import re
from os.path import exists, join, normpath, isdir


class Backup():
    src_dir = ''
    drive = ''
    dest_dir = ''

    def __init__(self):

        if len(sys.argv) == 3:

            if sys.argv[1] == 'code' and sys.argv[2] == 'external':

                self.src_dir = '/home/nikola/Documents/CODE'
                self.dest_dir = f'/media/nikola/External Disk/{self.get_root(self.src_dir)}'

            elif exists(sys.argv[1]) and exists(sys.argv[2]):

                self.src_dir = sys.argv[1]

                if exists(f'{sys.argv[2]}/{self.get_root(self.src_dir)}'):
                    self.dest_dir = sys.argv[2]
                else:
                    try:
                        mkdir(f'{sys.argv[2]}/{self.get_root(self.src_dir)}')
                    except OSError as e:
                        raise e
                    finally:
                        self.dest_dir = sys.argv[2]

                
            else:
                raise EnvironmentError('Invalid src/dest folders')

        else:

            raise EnvironmentError('Usage: <source_dir> <destination_dir>')

        print(self.src_dir, self.dest_dir)
        shutil.copytree(self.src_dir, self.dest_dir, ignore=self.ignore_list)


    def ignore_patterns(self, name, path):

        patterns = ['node_modules', '__pycache__']

        if isdir(path):

            if name in patterns:

                return True

        return False

    def ignore_list(self, path, files):

        filesToIgnore = []

        for fileName in files:

            fullFileName = join(normpath(path), fileName)

            if self.ignore_patterns(fileName, fullFileName):

                filesToIgnore.append(fileName)

            else:

                print(fileName)

        return filesToIgnore

    def get_root(self, dir):

        return re.findall('[a-zA-Z-_]*$', dir)[0]


if __name__ == '__main__':
    backup = Backup()
