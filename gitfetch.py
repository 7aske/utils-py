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
    pull_list = []
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
                self.repo_list.append(rf_abs)
                self.git(rf_abs, "fetch")

            else:
                for gf in listdir(rf_abs):
                    gf_abs = join(rf_abs, gf)
                    if isdir(gf_abs):
                        if ".git" in listdir(gf_abs):
                            self.repo_list.append(gf_abs)
                            self.git(gf_abs, "fetch")

        dialog_out = "\n"

        dialog_out += self.fetch_out(dialog_out)

        dialog_out += "\nRepositories checked: %d\n" % self.countern
        if self.counter > 0:
            dialog_out += "Repositories to pull: %d\n" % self.counter
        print(dialog_out)

        if self.counter > 0:
            self.pull()

    def pull(self):
        # Reseting for git pull
        for p in self.proc_list:
            p.kill()
        self.proc_list = []
        dialog_out = "\n"
        self.counter = 0
        # ----------------------

        answers = ["Y", "y", "N", "n"]
        answer = ""
        while answer not in answers:
            answer = input("Do you want to pull %d repositories?\n(Y/N): " % self.counter)
        if answer == "Y" or answer == "y":
            for repo in self.repo_list:
                self.git(repo, "pull")
            dialog_out += self.pull_out(dialog_out)
            dialog_out += "\nRepositories pulled: %d\n" % self.counter
            print(dialog_out)

    def pull_out(self, text):
        for i, p in enumerate(self.proc_list):
            out = str(p.stdout.read())
            if "Already up to date" not in out:
                text += self.repo_list[i] + "\n"
                self.counter += 1
            self.countern += 1
        return text

    def fetch_out(self, text):
        for i, p in enumerate(self.proc_list):
            out = str(p.stdout.read())
            if len(out) > 3:
                text += self.repo_list[i] + "\n"
                self.pull_list.append(self.repo_list[i])
                self.counter += 1
            self.countern += 1
        return text

    def git(self, path, action):
        p = Popen(["git", "-C", path, action], stderr=PIPE, stdout=PIPE)
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
