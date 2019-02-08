from os import listdir, getcwd, remove
from os.path import join, splitext, exists, isabs
from PIL import Image
from sys import argv
from instapy_cli import client
from time import sleep
from random import randrange, choice
import getpass
import configparser
from datetime import datetime as dt
from datetime import timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
    __next_upload = join(getcwd(), "nextupload")
    _bnw_caption = "#blackandwhitephotography #blackandwhite #streetphotography_bw #bw #bnw #bnwmood #bnw_captures #bnwphotography #bnw_mood #bnw_captures #bnwphotography"
    _regular_caption = "#vscofilm #vscodaily #vscocam #vsco #vscogood #vscoph #vsco_rs #vscogrid #vscomasters #vscobalkan #photography #fuji #explore #street #streetphotography #urban #urbanexploring #people #photojournalism"
    _timeout = 43200
    __dt_format = "%Y/%d/%m %H:%M:%S"
    __mail = False
    __mail_username = ""
    __mail_password = ""
    __mail_to = ""

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
                path = argv[argv.index("-f") + 1]
                self.__photos_dir = path if isabs(path) else join(getcwd(), path)
            elif "folder" in self.__config["config"]:
                path = self.__config["config"]["folder"]
                self.__photos_dir = path if isabs(path) else join(getcwd(), path)
            else:
                self.__photos_dir = getcwd()
            if "-t" in argv:
                try:
                    self._timeout = int(argv[argv.index("-t") + 1])
                except ValueError:
                    self._timeout = 43200
            elif "timeout" in self.__config["config"]:
                self._timeout = int(self.__config["config"]["timeout"])
            else:
                self._timeout = 43200

            self.__config["config"] = {
                "timeout": self._timeout,
                "folder": self.__photos_dir
            }

        except Exception:
            raise SystemExit("Usage: -f <folder> -t <timeout> [--watch] [--bedtime]")
        if not exists(self.__photos_dir):
            raise SystemExit("Photos directory doesn't exist.\n%s" % self.__photos_dir)
        with open(self.__config_path, "w") as configfile:
            self.__config.write(configfile)
            configfile.close()

        self.__mail = self.validate_mail_config()
        print(self.__mail)
        if self.__mail:
            self.__mail_username = self.__config["mailer"]["username"]
            self.__mail_password = self.__config["mailer"]["password"]
            self.__mail_to = self.__config["mailer"]["to"]

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
                    s = min(3600, self._timeout)
                    n = dt.now() + timedelta(seconds=s)
                    print("Next refresh - %s" % n.strftime(self.__dt_format))
                    sleep(s)
                else:
                    date = dt.now()
                    if exists(self.__next_upload):
                        with open(self.__next_upload, "r") as nextupload:
                            content = nextupload.read()
                            date = dt.strptime(content, self.__dt_format)
                    if dt.now() >= date:
                        self.update_tags()
                        try:
                            self.upload_photo()
                        except WrongPassword as e:
                            print(e)
                            raise SystemExit()
                        except ServerError as e:
                            print(e)
                            raise SystemExit()
                        s = self.get_timeout()
                        n = dt.now() + timedelta(seconds=s)
                        print("Next upload - %s" % n.strftime(self.__dt_format))
                        with open(self.__next_upload, "w") as nextupload:
                            nextupload.write(n.strftime(self.__dt_format))
                            nextupload.close()
                        if self.__mail:
                            self.send_email(n.strftime(self.__dt_format))
                            print("Mail sent")
                        sleep(s)
                    else:
                        newdate = date - dt.now()
                        print("Waiting for scheduled upload")
                        sleep(newdate.seconds + 1)
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
                bnw.close()
        if exists(regular_path):
            with open(regular_path, "r") as regular:
                self._regular_caption = ""
                for line in regular.readlines():
                    self._regular_caption += line
                regular.close()

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
                print(photo)
                cli.upload(photo, caption)
            remove(photo)
        except IOError as e:
            if "The password you entered is incorrect." in str(e):
                self.__config["credentials"]["password"] = ""
                with open(self.__config_path, "w") as configfile:
                    self.__config.write(configfile)
                    configfile.close()
                raise WrongPassword("Password The password you entered is incorrect. Please try again.")
            else:
                self.__photos.push(photo)
                print("Retrying photo upload in 60 seconds.")
                sleep(60)
                self.upload_photo()
        except Exception as e:
            raise ServerError(e)

    def get_timeout(self):
        offset = choice([-1, 1]) * randrange(int(self._timeout / 20), int(self._timeout / 10) + 1)
        return self._timeout + offset

    def validate_mail_config(self):
        if "mailer" in self.__config:
            if "to" in self.__config["mailer"] and "username" in self.__config["mailer"] and "password" in \
                    self.__config["mailer"]:
                return True
        return False

    def send_email(self, nextupload):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Instagram Upload"
        msg['From'] = self.__mail_username
        msg['To'] = self.__mail_to
        html = """\
        <html>
          <head></head>
          <body>
            New photo uploaded on account <b><a href="https://instagram.com/{account}">{account}</a></b>.<br><br>
            Next scheduled for: <u><b>{nextupload}</u></b>.<br><br>
            Remaining photos: <b>{remaining}</b>.
          </body>
        </html>
        """.format(account=self.__username, nextupload=nextupload, remaining=len(self.__photos))
        text = (
                "Subject: Instagram Upload\n\nNew photo uploaded on account %s.\n\nNext scheduled for: %s.\nRemaining photos: %d." % (
            self.__username, nextupload, len(self.__photos)))
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.__mail_username, self.__mail_password)
        server.sendmail(self.__mail_username, self.__mail_to, msg.as_string())
        server.quit()

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


class WrongPassword(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print("Wrong password")


class ServerError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print("Server Error")


if __name__ == '__main__':
    try:
        Main()
    except KeyboardInterrupt:
        raise SystemExit("\nBye")
