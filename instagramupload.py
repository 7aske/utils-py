from os import listdir, getcwd, remove
from os.path import join, splitext
from PIL import Image
from sys import argv
from instapy_cli import client
from time import sleep
from random import randrange
import getpass


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
    username = ""
    password = ""
    bnw_caption = ""
    regular_caption = "#vscofilm #vscodaily #vscocam #vsco #vscogood #vscoph #vsco_rs  #vscogrid #vscomasters #vscobalkan #photography #fuji #explore #street #streetphotography #urban #urbanexploring #people #photojournalism"
    photos = Stack()
    photos_dir = "#blackandwhitephotography #blackandwhite #streetphotography_bw #bw #bnw #bnwmood #bnw_captures #bnwphotography"
    timeout = 0

    def __init__(self):

        possible_answers = ["Y", "N"]
        answer = ""
        self.username = input("Username: ")
        self.password = getpass.unix_getpass("Password: ")
        if len(argv) == 3:
            self.timeout = int(argv[2])
            self.photos_dir = join(getcwd(), argv[1])
        elif len(argv) == 2:
            self.timeout = 43200
            self.photos_dir = join(getcwd(), argv[1])
        else:
            self.timeout = 43200
            self.photos_dir = getcwd()
        while answer.upper() not in possible_answers:
            print("Start uploading from:\n%s" % self.photos_dir)
            answer = input("Are you sure (Y/N)?")
        if answer.upper() == "Y":
            self.update_photos()
            while True:
                print(len(self.photos))
                if len(self.photos) == 0:
                    self.update_photos()
                else:
                    self.upload_photo()
                    s = self.get_timeout()
                    print(s)
                    sleep(s)
        else:
            SystemExit("Bye")

    def update_photos(self):
        for photo in listdir(self.photos_dir):
            _, ext = splitext(photo)
            if ext.upper() == ".JPG":
                self.photos.push(join(self.photos_dir, photo))

        if len(self.photos) == 0:
            raise SystemExit("Empty photos folder!")

    def upload_photo(self):
        photo = self.photos.pop()
        caption = self.regular_caption
        if self.is_bnw(photo):
            caption += "\n\n" + self.bnw_caption
        # TODO: FIX DIS
        with client(self.username, self.password) as cli:
            print(photo)
            try:
                cli.upload(photo, caption)
                remove(photo)
            except Exception as e:
                pass


    def get_timeout(self):
        val1 = self.timeout
        val2 = self.timeout + randrange(int(-1 * (self.timeout / 10)), int(self.timeout / 10) + 1)
        return randrange(min(val1, val2), max(val1, val2))

    def is_bnw(self, path):
        img = Image.open(path)
        pix = {"B": 0, "C": 0, "T": 0}
        w, h = img.size
        if w < h:
            print(w / h)
            if w / h < 0.8:
                blank = Image.new("RGB", (h, h), color=(255, 255, 255))
                new_img = blank.copy()
                offset = int((h - w) / 2)
                pos = (offset, 0)
                new_img.paste(img, pos)
                new_img.save(path)

        for i in range(int(w / 4)):
            for j in range(int(h / 4)):
                r, g, b = img.getpixel((i * 4, j * 4))
                if r != g != b:
                    pix["C"] += 1
                else:
                    pix["B"] += 1
                pix["T"] += 1
        try:
            out = pix["C"] / pix["T"]
        except ZeroDivisionError:
            out = 0
        return out < 0.2


if __name__ == '__main__':
    Main()
