#!/usr/bin/env python3

from os import remove, listdir, getenv
from sys import stdout
from shutil import rmtree
from os.path import join, isdir, isfile
import atexit

to_remove = ["node_modules", "__pycache__"]
def main():
    folder = getenv("CODE")
    if folder is not None:
        answers = ["Y", "N"]
        answer = ""
        print("Cleaning {}".format(folder))
        while answer.upper() not in answers:
            answer = input("Are you sure? ")
        if answer.upper() == "Y":
            clean_files(folder)
        else:
            raise SystemExit

def clean_files(path):
        for f in listdir(path):
            abs_path = join(path, f)
            if isdir(abs_path):
                if f in to_remove:
                    if input("Delete " + abs_path + "? (Y/N) ").upper() == "Y":
                        try:
                            rmtree(abs_path)
                            print("Deleted " + abs_path)
                        except PermissionError:
                            print("EPERM: Error accessing: " + abs_path)

                else:
                    clean_files(abs_path)
            elif isfile(abs_path):
                if f in to_remove:
                    if input("Delete " + abs_path + "? (Y/N) ").upper() == "Y":
                        try:
                            remove(abs_path)
                            print("Deleted " + abs_path)
                        except PermissionError:
                            print("EPERM: Error accessing: " + abs_path)


@atexit.register
def clear():
    stdout.write('\n')



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye")
    except SystemExit:
        print("\nBye")
