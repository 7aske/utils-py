from json import load
from sys import platform, argv
from os import listdir, getcwd
from os.path import isdir, join, dirname
from subprocess import Popen, PIPE


class Status:
    repo_list = []
    proc_list = []
    setings = {}
    counter = 0
    countern = 0
    src = ""

    def __init__(self):
        with open(join(dirname(__file__), "settings.json")) as f:
            self.settings = load(f)
        if len(argv) == 2:
            self.src = self.parse_path(argv[1])
        else:
            self.src = self.settings[platform]["code"]

        self.check(self.src)

    def check(self, path):

        for rf in listdir(path):
            rf_abs = join(path, rf)
            if ".git" in listdir(rf_abs):
                self.git_status(rf_abs)

            for gf in listdir(rf_abs):
                gf_abs = join(rf_abs, gf)
                if isdir(gf_abs):
                    if ".git" in listdir(gf_abs):
                        self.git_status(gf_abs)

        dialog_out = "\n"
        for i, p in enumerate(self.proc_list):
            out = str(p.stdout.read())
            if self.check_errors(out):
                dialog_out += "%s \n" % self.repo_list[i]
                self.counter += 1
            self.countern += 1

        dialog_out += "\nRepositories checked: %d\n" % self.countern
        if self.counter > 0:
            dialog_out += "Not up-to-date: %d\n" % self.counter
        print(dialog_out)

    def git_status(self, path):
        self.repo_list.append(path)
        p = Popen(["git", "-C", path, "status"], stderr=PIPE, stdout=PIPE)
        self.proc_list.append(p)

    def check_errors(self, s):
        errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
        for error in errors:
            if error in s:
                return True
        return False

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
            return join(getcwd(), path[2:])
        elif path.startswith('.'):
            return getcwd()


if __name__ == "__main__":
    Status()
