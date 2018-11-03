from json import load
from sys import platform
from subprocess import check_output, STDOUT
from os import listdir
from os.path import isdir, join, dirname, basename


class Status:
    src_dir = ''
    fld_list = []
    setings = {}
    slash = "\\" if platform == "win32" else '/'
    counter = 0
    countern = 0

    def __init__(self):
        with open(join(dirname(__file__), "settings.json")) as f:
            self.settings = load(f)
        self.src_dir = self.settings[platform]["code"]
        self.check()

    def check(self):

        for rf in listdir(self.src_dir):
            rf_abs = self.src_dir + self.slash + rf
            if ".git" in listdir(rf_abs):
                self.fld_list.append(rf_abs)
            for gf in listdir(rf_abs):
                gf_abs = rf_abs + self.slash + gf
                if isdir(gf_abs):
                    self.fld_list.append(gf_abs)
        for f in self.fld_list:
            if ".git" in listdir(f):
                try:
                    out = str(check_output(f"git -C \"{f}\" status", stderr=STDOUT))
                except Exception as e:
                    out = str(e.output)
                if not "Your branch is up to date" or "Changes not staged" in out:
                    print("Not up-to-date", end=" - ")
                    print(basename(f))
                    self.countern += 1

                self.counter += 1
        print("Repositories checked: %d" % self.counter)
        if self.countern > 0:
            print("Not up-to-date: %d" % self.countern)


if __name__ == "__main__":
    Status()
