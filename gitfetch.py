from sys import platform
from json import load
from os.path import dirname, join, isdir
from os import listdir
from subprocess import Popen, PIPE


class Fetch:
    settings: {}
    counter = 0
    repo_list = []
    proc_list = []

    def __init__(self):
        self.settings = load(open(join(dirname(__file__), "settings.json")))
        answers = ["Y", "y", "N", "n"]
        answer = ' '
        print("Fetch all repositories in folder \n%s (Y/N):" % self.settings[platform]["code"], end=" ")
        while answer not in answers:
            answer = input()
        if answer in ["Y", "y"]:
            self.fetch()

    def fetch(self):
        for folder in listdir(self.settings[platform]["code"]):
            rf = join(self.settings[platform]["code"], folder)
            if ".git" in listdir(rf):
                self.repo_list.append(rf)
            else:
                for rfolder in listdir(rf):
                    gf = join(rf, rfolder)
                    if isdir(gf):
                        if ".git" in listdir(gf):
                            self.repo_list.append(gf)

        for repo in self.repo_list:
            p = Popen(["git", "-C", repo, "fetch"], stderr=PIPE, stdout=PIPE)
            self.proc_list.append(p)
        c = 0
        for p in self.proc_list:
            out = str(p.stdout.read())

            if len(out) > 3:
                print(self.repo_list[c])
                self.counter += 1
            c += 1
        print("Repositories to pull: %d" % self.counter)

    #
    # def check_errors(self, str):
    #     errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
    #     for error in errors:
    #         if error in str:
    #             return True
    #     return False


if __name__ == "__main__":
    fetch = Fetch()
