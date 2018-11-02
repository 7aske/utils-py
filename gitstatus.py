from json import load
from sys import platform
from subprocess import check_output, STDOUT
from os import listdir, walk
from os.path import isdir


class Status:
    src_dir = ''
    fld_list = []
    setings = {}
    slash = "\\" if platform == "win32" else '/'

    def __init__(self):
        with open("settings.json") as f:
            self.settings = load(f)
        self.src_dir = self.settings[platform]["code"]

        for rf in listdir(self.src_dir):
            rf_abs = self.src_dir + self.slash + rf
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
                if "Changes not staged for commit" in out:
                    print("Not up-to-date")
                    print(f)
                else:
                    print("Up-to-date")


if __name__ == "__main__":
    status = Status()
