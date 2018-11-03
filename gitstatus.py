from json import load
from sys import platform
from subprocess import check_output, STDOUT
from os import listdir
from os.path import isdir, join, dirname, basename


class Status:
    fld_list = []
    setings = {}
    counter = 0
    countern = 0

    def __init__(self):
        with open(join(dirname(__file__), "settings.json")) as f:
            self.settings = load(f)
        self.check()

    def check(self):

        for rf in listdir(self.settings[platform]["code"]):
            rf_abs = join(self.settings[platform]["code"], rf)
            if ".git" in listdir(rf_abs):
                self.fld_list.append(rf_abs)
            for gf in listdir(rf_abs):
                gf_abs = join(rf_abs, gf)
                if isdir(gf_abs):
                    self.fld_list.append(gf_abs)
        dialog_out = ""
        for f in self.fld_list:
            if ".git" in listdir(f):
                try:
                    out = str(check_output(f"git -C \"{f}\" status", stderr=STDOUT))
                except Exception as e:
                    out = str(e.output)
                if self.check_errors(out):
                    dialog_out +="Not up-to-date - " + basename(f) + "\n"
                    self.countern += 1

                self.counter += 1
        dialog_out += "\nRepositories checked: %d\n" % self.counter
        if self.countern > 0:
            dialog_out += "Not up-to-date: %d\n" % self.countern
        print(dialog_out)

    def check_errors(self, str):
        errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
        for error in errors:
            if error in str:
                return True
        return False


if __name__ == "__main__":
    Status()
