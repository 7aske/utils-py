#!/usr/bin/python3

import atexit
from filecmp import cmp
import getpass
from os.path import exists, isdir, isfile, getmtime, join, basename, isabs
from os import getcwd, listdir, remove, walk, makedirs, chmod
import pysftp as sftp
from pysftp import CnOpts
import re
from shutil import copy2, rmtree
from sys import argv, platform, stdout, warnoptions
from subprocess import check_output
import configparser
from pathlib import Path
import warnings

if not warnoptions:
    warnings.simplefilter("ignore")


class Backup:
    src_dir = ''
    dest_dir = ''
    username = ''
    hostname = ''
    password = ''
    files_total = 0
    files_count = 0
    config = configparser.ConfigParser()
    config_path_home = join(str(Path.home()), "backup.ini")
    config_path = join(getcwd(), "backup.ini")
    remote = False
    clean = False

    def __init__(self):
        if "--remote" in argv:
            self.remote = True
        if "--clean" in argv:
            self.clean = True

        if exists(self.config_path_home):
            self.config.read(self.config_path_home)
        elif exists(self.config_path):
            self.config.read(self.config_path)

        if exists(self.config_path_home) or exists(self.config_path):
            if platform not in self.config.keys():
                raise SystemExit("Invalid config file")
            if "src" not in self.config[platform].keys() or "dest" not in self.config[platform].keys():
                raise SystemExit("Invalid config file")
            self.src_dir = self.config[platform]["src"]
            dest_dir = self.config[platform]["dest"]
            if dest_dir.endswith(basename(self.src_dir)):
                self.dest_dir = dest_dir
            else:
                self.dest_dir = join(self.config[platform]["dest"], basename(self.src_dir))

        if "-f" in argv:
            try:
                path = argv[argv.index("-f") + 1]

                if isabs(path):
                    self.src_dir = path
                else:
                    self.src_dir = join(getcwd(), self.format_path(path))

                if "shortcuts" in self.config.keys():
                    if path in self.config["shortcuts"]:
                        self.src_dir = self.config["shortcuts"][path]
            except IndexError:
                print("Invalid source argument")

        if "-d" in argv:
            try:
                path = argv[argv.index("-d") + 1]

                if isabs(path):
                    self.dest_dir = join(path, basename(self.src_dir))
                else:
                    self.dest_dir = join(getcwd(), self.format_path(path))

                if "shortcuts" in self.config.keys():
                    if path in self.config["shortcuts"]:
                        self.dest_dir = join(self.config["shortcuts"][path], basename(self.src_dir))
            except IndexError:
                print("Invalid source argument")

        if self.remote:
            if "-d" not in argv:
                self.src_dir = self.config[platform]["src"]
                dest_dir = self.config["remote"]["dest"]

                if dest_dir.endswith(basename(self.src_dir)):
                    self.dest_dir = dest_dir
                else:
                    self.dest_dir = join(self.config["remote"]["dest"], basename(self.src_dir))

            if len(self.config["remote"]["hostname"]) == 0:
                self.hostname = input('Hostname:')
            else:
                self.hostname = self.config["remote"]["hostname"]

            if len(self.config["remote"]["username"]) == 0:
                self.username = input('Username:')
                self.config["remote"]["username"] = self.username

            else:
                self.username = self.config["remote"]["username"]

            if len(self.config["remote"]["password"]) == 0:
                self.password = getpass.win_getpass('Password:') if platform == 'win32' else getpass.unix_getpass(
                    'Password:')
            else:
                self.password = self.config["remote"]["password"]

        if not exists(self.src_dir) or not isdir(self.src_dir):
            raise SystemExit('Invalid source dir')
        if len(self.dest_dir) == 0:
            raise SystemExit('Invalid destination dir')

        print(f'Source      {self.src_dir}')
        if self.remote:
            print(f'Destination {self.username}@{self.hostname}:{self.dest_dir}')
        elif not self.clean:
            print(f'Destination {self.dest_dir}')
        elif self.clean:
            if "delete" not in self.config.keys():
                raise SystemExit("Invalid delete config")
            elif "files" not in self.config["delete"].keys() and "folders" not in self.config["delete"].keys():
                raise SystemExit("Invalid delete config")
            elif len(self.config["delete"]["files"]) == 0 and len(self.config["delete"]["folders"]) == 0:
                raise SystemExit("Invalid delete config")
            print("Cleaning selected directory")
        answer = ''
        possible_answers = ['Y', 'y', 'N', 'n']
        while answer not in possible_answers:
            answer = input('Proceed? (Y/N) ')

        if answer.upper() == "Y":

            if self.clean:
                if "delete" not in self.config.keys():
                    raise SystemExit("Invalid delete config")
                elif "files" not in self.config["delete"].keys() and "folders" not in self.config["delete"].keys():
                    raise SystemExit("Invalid delete config")
                elif len(self.config["delete"]["files"]) == 0 and len(self.config["delete"]["folders"]) == 0:
                    raise SystemExit("Invalid delete config")
                self.clean_files(self.src_dir)
            elif self.remote:
                self.files_total = self.count_files(self.src_dir)
                self.make_dest_dir()
                self.connect()
            else:
                self.files_total = self.count_files(self.src_dir)
                self.make_dest_dir()
                self.backup_files(self.src_dir)
                answer = ""
                while answer not in possible_answers:
                    answer = input("\nDo you want to clean dest dir? (Y/N) ")
                if answer.upper() == "Y":
                    self.rm_old(self.dest_dir)
                else:
                    raise SystemExit("Bye!")
        else:
            raise SystemExit('Bye!')

    def rm_old(self, path):
        for f in listdir(path):
            abs_path = join(path, f)
            src_path = join(self.src_dir, self.get_rel_path_rm(abs_path))
            if isdir(abs_path):
                if not exists(src_path):
                    try:
                        print(abs_path)
                        rmtree(abs_path)
                    except OSError:
                        print("Error deleting: %s" % src_path)
                else:
                    self.rm_old(abs_path)
            elif isfile(abs_path):
                if not exists(src_path):
                    print(abs_path)
                    remove(abs_path)

    def backup_files(self, path):
        for f in listdir(path):
            abs_path = join(path, f)
            dest_path = self.dest_dir + self.get_rel_path(abs_path)

            if isdir(abs_path) and not self.to_ignore(abs_path):
                if not exists(dest_path):
                    makedirs(dest_path)
                try:
                    self.backup_files(abs_path)
                except PermissionError:
                    print(f"EPERM: Error copying {abs_path}")

            elif isfile(abs_path) and not self.to_ignore(abs_path):
                if not exists(dest_path):
                    try:
                        copy2(abs_path, dest_path)
                    except PermissionError:
                        print(f"EPERM: Error copying {dest_path}")
                    except OSError:
                        raise SystemExit(f'Error copying {dest_path}')

                else:
                    if not cmp(abs_path, dest_path):
                        if getmtime(abs_path) > getmtime(dest_path):
                            try:
                                copy2(abs_path, dest_path)
                            except PermissionError:
                                print(f"EPERM: Error copying {dest_path}")
                            except OSError:
                                raise SystemExit(f'Error replacing {dest_path}')

                self.files_count += 1
            self.progress(self.files_count, self.files_total)

    def clean_files(self, path):
        for f in listdir(path):
            abs_path = join(path, f)
            if isdir(abs_path):
                if self.to_remove(abs_path):
                    if input("Delete " + abs_path + "? (Y/N) ").upper() == "Y":
                        try:
                            rmtree(abs_path)
                            print("Deleted " + abs_path)
                        except PermissionError:
                            print("EPERM: Error accessing: " + abs_path)

                else:
                    self.clean_files(abs_path)
            elif isfile(abs_path):
                if self.to_remove(abs_path):
                    if input("Delete " + abs_path + "? (Y/N) ").upper() == "Y":
                        try:
                            remove(abs_path)
                            print("Deleted " + abs_path)
                        except PermissionError:
                            print("EPERM: Error accessing: " + abs_path)

    def connect(self):
        opts = CnOpts()
        opts.hostkeys = None
        try:
            conn = sftp.Connection(self.hostname, username=self.username, password=self.password, cnopts=opts)
        except ConnectionError:
            raise SystemExit("Connection error")
        self.backup_files_network(self.src_dir, conn)

    def backup_files_network(self, path, conn):
        for f in listdir(path):
            abs_path = join(path, f)
            relative_path = self.get_rel_path(abs_path)
            dest_path = self.dest_dir + relative_path

            if isdir(abs_path) and not self.to_ignore(abs_path):
                if f == '.git':
                    try:
                        out = check_output(['git', '-C', abs_path, 'remote', '-v']).decode()
                        git = re.findall('https://.*github.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_]+', out)[0]
                    except IndexError:
                        raise SystemExit(f'Bad git remote {abs_path}')
                    try:
                        gitp = abs_path[:-4] + 'gitp'
                        gitp_file = open(gitp, 'w')
                        gitp_file.write(
                            f'git init && git remote add origin {git}'
                            f' && git fetch origin master && git reset --hard origin/master && git pull origin master')
                        gitp_file.close()
                        gitp_path = dest_path[:-4] + 'gitp'
                        chmod(gitp, 775)
                        conn.put(gitp, remotepath=gitp_path)
                        remove(gitp)
                    except OSError:
                        raise SystemExit('Cannot write git command file')
                    self.files_count += self.count_files(abs_path)
                else:
                    if not conn.exists(dest_path):
                        conn.makedirs(dest_path)
                    self.backup_files_network(abs_path, conn)

            elif isfile(abs_path) and not self.to_ignore(abs_path):

                self.files_count += 1
                conn.put(abs_path, remotepath=dest_path, preserve_mtime=True)
            self.progress(self.files_count, self.files_total)

    def to_ignore(self, path):
        if isdir(path):
            try:
                folders = self.config["ignore"]["folders"].split(", ")
            except Exception as e:
                print(e)
                folders = []
            if basename(path) in folders:
                return True
        elif isfile(path):
            try:
                files = self.config["ignore"]["files"].split(", ")
            except Exception as e:
                print(e)
                files = []
            if basename(path) in files:
                return True
        return False

    def to_remove(self, path):
        base = basename(path)
        if isdir(path):
            if base in self.config["delete"]["folders"].split(", "):
                return True
        elif isfile(base):
            if base in self.config["delete"]["files"].split(", "):
                return True
        return False

    def get_rel_path(self, path):
        base = basename(self.src_dir)
        return path[path.index(base) + len(base):]

    def get_rel_path_rm(self, path):
        return path[path.index(basename(self.dest_dir)) + len(basename(self.dest_dir)) + 1:]

    def make_dest_dir(self):
        if self.remote:
            with sftp.Connection(self.hostname, username=self.username, password=self.password) as conn:
                if not conn.exists(self.dest_dir):
                    conn.makedirs(self.dest_dir)
        else:
            if not exists(self.dest_dir):
                try:
                    makedirs(self.dest_dir)
                except OSError:
                    raise SystemExit('Invalid dest directory')

    @staticmethod
    def format_path(path):
        if path.startswith("./"):
            return path[2:]
        elif path == ".":
            return ""
        else:
            return path

    @staticmethod
    def count_files(path):
        return sum([len(f) for _, _, f in walk(path)])

    @staticmethod
    def progress(count, total):
        bar_len = 50
        filled_len = int(round(bar_len * count / float(total)))
        status = f"{count}/{total}"
        percents = round(100.0 * count / float(total), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        stdout.write('[%s] %.2f%s Files: %s \r' % (bar, percents, '%', status))
        stdout.flush()


@atexit.register
def clear():
    stdout.write('\n')


if __name__ == '__main__':
    try:
        Backup()
    except KeyboardInterrupt:
        print("\nBye")
