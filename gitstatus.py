from os import listdir, getcwd
from os.path import isdir, join, exists
from subprocess import Popen, PIPE
import configparser
from pathlib import Path
from sys import argv


class Status:
    repo_list = []
    proc_list = []
    config = configparser.ConfigParser()
    config_path = join(getcwd(), "gitstatus.ini")
    config_path_home = join(str(Path.home()), "gitstatus.ini")
    counter = 0
    countern = 0
    src = ""

    def __init__(self):
        if exists(self.config_path):
            self.config.read(self.config_path)
            self.src = self.config["path"]["src"]
        elif exists(self.config_path_home):
            self.config.read(self.config_path_home)
            self.src = self.config["path"]["src"]
        else:
            raise SystemExit("Invalid config file")

        if len(argv) == 2:
            self.src = join(self.src, argv[1])

        self.check(self.src)

    def check(self, path):

        for rf in listdir(path):
            rf_abs = join(path, rf)
            if isdir(rf_abs) and not self.ignore(rf, rf_abs):
                if rf == ".git":
                    self.git_status(path)
                elif ".git" in listdir(rf_abs):
                    self.git_status(rf_abs)

                for gf in listdir(rf_abs):
                    gf_abs = join(rf_abs, gf)
                    if isdir(gf_abs):
                        if ".git" in listdir(gf_abs):
                            self.git_status(gf_abs)

        dialog_out = self.proc_out("\n")

        dialog_out += "\nRepositories checked: %d\n" % self.countern
        if self.counter > 0:
            dialog_out += "Not up-to-date: %d\n" % self.counter
        print(dialog_out)

    def git_status(self, path):
        self.repo_list.append(path)
        p = Popen(["git", "-C", path, "status"], stderr=PIPE, stdout=PIPE)
        self.proc_list.append(p)

    def proc_out(self, text):
        for i, p in enumerate(self.proc_list):
            out = str(p.stdout.read())
            if self.check_errors(out):
                text += "%s \n" % self.repo_list[i]
                self.counter += 1
            self.countern += 1
        return text

    @staticmethod
    def check_errors(s):
        errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
        for error in errors:
            if error in s:
                return True
        return False

    @staticmethod
    def ignore(name, path):
        ignore_folders = ["_test", "_others"]
        if isdir(path):
            if name in ignore_folders:
                return True
        return False


if __name__ == "__main__":
    try:
        Status()
    except KeyboardInterrupt:
        raise SystemExit("\nBye")
