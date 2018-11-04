from sys import platform, argv
from json import load
from os.path import dirname, join, isdir
from os import listdir, getcwd
from subprocess import Popen, PIPE


class Fetch:
    settings: {}
    counter = 0
    countern = 0
    repo_list = []
    proc_list = []
    src = ""

    def __init__(self):
        self.settings = load(open(join(dirname(__file__), "settings.json")))
        if len(argv) == 2:
            self.src = self.parse_path(argv[1])
        else:
            self.src = self.settings[platform]["code"]

        answers = ["Y", "y", "N", "n"]
        answer = ' '
        print("Fetch all repositories in folder?\n%s\n(Y/N):" % self.src, end=" ")
        while answer not in answers:
            answer = input()
        if answer in ["Y", "y"]:
            self.fetch(self.src)

    def fetch(self, path):
        for rf in listdir(path):

            rf_abs = join(path, rf)

            if ".git" in listdir(rf_abs):
                self.git_fetch(rf_abs)

            else:
                for gf in listdir(rf_abs):
                    gf_abs = join(rf_abs, gf)
                    if isdir(gf_abs):
                        if ".git" in listdir(gf_abs):
                            self.git_fetch(gf_abs)

        dialog_out = "\n"

        for i, p in enumerate(self.proc_list):
            out = str(p.stdout.read())
            if len(out) > 3:
                dialog_out += self.repo_list[i] + "\n"
                self.counter += 1
            self.countern += 1

        dialog_out += "\nRepositories checked: %d\n" % self.countern

        if self.counter > 0:
            dialog_out += "Repositories to pull: %d\n" % self.counter

        print(dialog_out)

    def git_fetch(self, path):
        self.repo_list.append(path)
        p = Popen(["git", "-C", path, "fetch"], stderr=PIPE, stdout=PIPE)
        self.proc_list.append(p)

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
    fetch = Fetch()
