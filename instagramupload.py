from os import listdir, getcwd, remove
from os.path import join, splitext, exists
from PIL import Image
from sys import argv
from instapy_cli import client
from time import sleep
from random import randrange, choice
import getpass
import configparser
from datetime import datetime as dt


class Stack:
    def __init__(self):
        self.items = []

    def __repr__(self):
        return str([item for item in self.items])

    def __len__(self):
        return len(self.items)

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def is_empty(self):
        return self.items == []


class Main:
    __username = ""
    __password = ""
    __watch = False
    __bedtime = False
    __photos = Stack()
    __photos_dir = ""
    __config = configparser.ConfigParser()
    __config_path = join(getcwd(), "instagramupload.ini")
    _bnw_caption = "#blackandwhitephotography #blackandwhite #streetphotography_bw #bw #bnw #bnwmood #bnw_captures #bnwphotography #bnw_mood #bnw_captures #bnwphotography"
    _regular_caption = "#vscofilm #vscodaily #vscocam #vsco #vscogood #vscoph #vsco_rs #vscogrid #vscomasters #vscobalkan #photography #fuji #explore #street #streetphotography #urban #urbanexploring #people #photojournalism"
    _timeout = 43200

    def __init__(self):

        if "--watch" in argv:
            self.__watch = True
            print("Starting in watch mode.")
            argv.remove("--watch")
        if "--bedtime" in argv:
            print("Starting in no bedtime mode.")
            self.__watch = True
            argv.remove("--bedtime")

        possible_answers = ["Y", "N"]
        answer = ""
        if exists(self.__config_path):
            self.__config.read(self.__config_path)
            if "credentials" not in self.__config:
                raise SystemExit("Bad config file.")
            else:
                if "username" not in self.__config["credentials"] or "password" not in self.__config["credentials"]:
                    raise SystemExit("Bad config file.")

            self.__config.read(self.__config_path)
            self.__username = self.__config["credentials"]["username"]
            self.__password = self.__config["credentials"]["password"]
            print("Account: %s" % self.__username)
            if self.__username == "":
                raise SystemExit("Invalid instagramupload.ini username.")
            if self.__password == "":
                self.__password = getpass.unix_getpass("Password: ")

            print("Password: %s" % "".join(["*" for _ in self.__password]))

        else:
            self.__username = input("Username: ")
            self.__password = getpass.unix_getpass("Password: ")
            self.__config["credentials"] = {
                "username": self.__username,
                "password": self.__password
            }
            with open(self.__config_path, "w") as configfile:
                self.__config.write(configfile)
                configfile.close()

        try:

            if "-f" in argv:
                self.__photos_dir = join(getcwd(), argv[argv.index("-f") + 1])
            else:
                self.__photos_dir = getcwd()
            if "-t" in argv:
                try:
                    self._timeout = int(argv[argv.index("-t") + 1])
                except ValueError:
                    self._timeout = 43200
            else:
                self._timeout = 43200
        except Exception:
            raise SystemExit("Usage: -f <folder> -t <timeout> [--watch] [--bedtime]")

        if not exists(self.__photos_dir):
            raise SystemExit("Photos directory doesn't exist.\n%s" % self.__photos_dir)

        while answer.upper() not in possible_answers:
            print("Start uploading from: '%s'" % self.__photos_dir, end="")
            print(" with timeout of '%d'" % self._timeout)
            answer = input("Are you sure? (Y/N) ")
        if answer.upper() == "Y":
            self.update_photos()
            while True:
                print("Photos - %d" % len(self.__photos))
                if len(self.__photos) == 0:
                    self.update_photos()
                    print("Timeout - %d" % min(3600, self._timeout))
                    sleep(min(3600, self._timeout))
                else:
                    self.update_tags()
                    self.upload_photo()
                    s = self.get_timeout()
                    print("Timeout - %d" % s)
                    sleep(s)
        else:
            raise SystemExit("Bye")

    def update_photos(self):
        for photo in listdir(self.__photos_dir):
            _, ext = splitext(photo)
            if ext.upper() == ".JPG":
                self.__photos.push(join(self.__photos_dir, photo))

        if len(self.__photos) == 0:
            if not self.__watch:
                raise SystemExit("Folder Empty")

    def update_tags(self):
        bnw_path = join(getcwd(), "bnw_tags.txt")
        regular_path = join(getcwd(), "regular_tags.txt")
        if exists(bnw_path):
            with open(bnw_path, "r") as bnw:
                self._bnw_caption = ""
                for line in bnw.readlines():
                    self._bnw_caption += line
        if exists(regular_path):
            with open(bnw_path, "r") as regular_path:
                self._regular_caption = ""
                for line in regular_path.readlines():
                    self._regular_caption += line

    def upload_photo(self):
        if 1 < dt.now().hour < 9 and self.__bedtime:
            print("Bed time, skipping upload")
            pass
        photo = self.__photos.pop()
        caption = self._regular_caption
        if self.is_bnw(photo):
            caption += "\n\n" + self._bnw_caption
        try:
            with client(self.__username, self.__password) as cli:
                print(caption)
                cli.upload(photo, caption)
                remove(photo)
        except IOError as e:
            if "The password you entered is incorrect." in str(e):
                self.__config["credentials"]["password"] = ""
                with open(self.__config_path, "w") as configfile:
                    self.__config.write(configfile)
                    configfile.close()
                raise SystemExit("Password The password you entered is incorrect. Please try again.")
            self.__photos.push(photo)
            print("Retrying photo upload in 60 seconds.")
            sleep(60)
            self.upload_photo()

    def get_timeout(self):
        offset = choice([-1, 1]) * randrange(int(self._timeout / 20), int(self._timeout / 10) + 1)
        return self._timeout + offset

    @staticmethod
    def is_bnw(path):
        img = Image.open(path)
        w, h = img.size
        pix = {"B": 0, "C": 0, "T": 0}
        for i in range(int(w / 4)):
            for j in range(int(h / 4)):
                r, g, b = img.getpixel((i * 4, j * 4))
                if r != g != b:
                    pix["C"] += 1
                else:
                    pix["B"] += 1
                pix["T"] += 1

        if w < h:
            if w / h < 0.8:
                blank = Image.new("RGB", (h, h), color=(255, 255, 255))
                new_img = blank.copy()
                offset = int((h - w) / 2)
                pos = (offset, 0)
                new_img.paste(img, pos)
                new_img.save(path)
                new_img.close()
                blank.close()

        try:
            out = pix["C"] / pix["T"]
            return out < 0.2
        except ZeroDivisionError:
            out = 0
            return out < 0.2
        finally:
            img.close()


if __name__ == '__main__':
    Main()
