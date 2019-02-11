import atexit
from os import listdir, getcwd, remove, rename
from os.path import join, splitext, exists, isabs
from PIL import Image
from sys import argv
import sys
from instapy_cli import client
from time import sleep
from random import randrange, choice
import getpass
import configparser
from datetime import datetime as dt
from datetime import timedelta
import smtplib
from pathlib import Path
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


class Logger:
    file = ""
    out = True
    dt_format = "%d/%m %H:%M:%S"

    def __init__(self, file, out=True):
        self.out = out
        self.file = join(str(Path.home()), file)

    def log(self, data):
        output = "{}:\t{}".format(dt.now().strftime("%m/%d %H:%M:%S"), data + "\n")
        if self.out:
            with open(self.file, "a+") as f:
                f.write(output)
        print(data)


class Main:
    username = ""
    password = ""
    watch = False
    bedtime = False
    photos = Stack()
    photos_dir = ""
    config = configparser.ConfigParser()
    config_path = join(getcwd(), "instagramupload.ini")
    next_upload = join(getcwd(), "nextupload")
    bnw_caption = "#blackandwhitephotography #blackandwhite #streetphotography_bw #bw #bnw #bnwmood #bnw_captures #bnwphotography #bnw_mood #bnw_captures #bnwphotography"
    regular_caption = "#vscofilmscodaily #vscocam #vsco #vscogood #vscoph #vsco_rs #vscogrid #vscomasters #vscobalkan #photography #fuji #explore #street #streetphotography #urban #urbanexploring #people #photojournalism"
    timeout = 4320
    dt_format = "%Y/%d/%m %H:%M:%S"
    mail = False
    mail_username = ""
    mail_password = ""
    mail_to = ""
    logger = None

    def __init__(self):

        self.logger = Logger("instaupload.log")
        if "--watch" in argv:
            self.watch = True
            self.logger.log("Starting in watch mode.")
            argv.remove("--watch")
        if "--bedtime" in argv:
            self.logger.log("Starting in no bedtime mode.")
            self.watch = True
            argv.remove("--bedtime")

        possible_answers = ["Y", "N"]
        answer = ""
        if exists(self.config_path):
            self.config.read(self.config_path)
            if "credentials" not in self.config:
                raise SystemExit("Bad config file.")
            else:
                if "username" not in self.config["credentials"] or "password" not in self.config["credentials"]:
                    raise SystemExit("Bad config file.")

            self.config.read(self.config_path)
            self.username = self.config["credentials"]["username"]
            self.password = self.config["credentials"]["password"]
            print("Account: %s" % self.username)
            if self.username == "":
                raise SystemExit("Invalid instagramupload.ini username.")
            if self.password == "":
                self.password = getpass.unix_getpass("Password: ")

            print("Password: %s" % "".join(["*" for _ in self.password]))

        else:
            self.username = input("Username: ")
            self.password = getpass.unix_getpass("Password: ")
            self.config["credentials"] = {
                "username": self.username,
                "password": self.password
            }
            with open(self.config_path, "w") as configfile:
                self.config.write(configfile)
        try:
            if "-f" in argv:
                path = argv[argv.index("-f") + 1]
                self.photos_dir = path if isabs(path) else join(getcwd(), path)
            elif "folder" in self.config["config"]:
                path = self.config["config"]["folder"]
                self.photos_dir = path if isabs(path) else join(getcwd(), path)
            else:
                self.photos_dir = getcwd()
            if "-t" in argv:
                try:
                    self.timeout = int(argv[argv.index("-t") + 1])
                except ValueError:
                    self.timeout = 43200
            elif "timeout" in self.config["config"]:
                self.timeout = int(self.config["config"]["timeout"])
            else:
                self.timeout = 43200

            self.config["config"] = {
                "timeout": self.timeout,
                "folder": self.photos_dir
            }

        except Exception:
            raise SystemExit("Usage: -f <folder> -t <timeout> [--watch] [--bedtime]")
        if not exists(self.photos_dir):
            raise SystemExit("Photos directory doesn't exist.\n%s" % self.photos_dir)
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)

        self.mail = self.validate_mail_config()
        if self.mail:
            self.mail_username = self.config["mailer"]["username"]
            self.mail_password = self.config["mailer"]["password"]
            self.mail_to = self.config["mailer"]["to"]

        while answer.upper() not in possible_answers:
            print("Start uploading from: '%s'" % self.photos_dir, end="")
            print(" with timeout of '%d'" % self.timeout)
            answer = input("Are you sure? (Y/N) ")
        if answer.upper() == "Y":
            self.update_photos()
            try:
                while True:
                    self.logger.log("Photos - %d" % len(self.photos))
                    if len(self.photos) == 0:
                        self.update_photos()
                        s = min(3600, self.timeout)
                        n = dt.now() + timedelta(seconds=s)
                        self.logger.log("Next refresh - %s" % n.strftime(self.dt_format))
                        sleep(s)
                    else:
                        date = dt.now()
                        if exists(self.next_upload):
                            with open(self.next_upload, "r") as nextupload:
                                content = nextupload.read()
                                date = dt.strptime(content, self.dt_format)
                        if dt.now() >= date:
                            self.update_tags()
                            try:
                                self.upload_photo()
                            except WrongPassword as e:
                                self.logger.log(str(e))
                                raise SystemExit()
                            except ServerError as e:
                                self.logger.log(str(e))
                                raise SystemExit()
                            s = self.get_timeout()
                            n = dt.now() + timedelta(seconds=s)
                            self.logger.log("Next upload - %s" % n.strftime(self.dt_format))
                            with open(self.next_upload, "w") as nextupload:
                                nextupload.write(n.strftime(self.dt_format))
                            if self.mail:
                                self.send_email(n.strftime(self.dt_format))
                                self.logger.log("Mail sent")
                            sleep(s)
                        else:
                            newdate = date - dt.now()
                            self.logger.log("Waiting for scheduled upload")
                            self.logger.log("Next upload - %s" % date.strftime(self.logger.dt_format))
                            sleep(newdate.seconds + 1)
            except KeyboardInterrupt:
                self.logger.log("\r**************************")
        else:
            raise SystemExit("Bye")

    def update_photos(self):
        for photo in listdir(self.photos_dir):
            _, ext = splitext(photo)
            if ext.upper() == ".JPG":
                self.photos.push(join(self.photos_dir, photo))

        if len(self.photos) == 0:
            if not self.watch:
                self.logger.log("Folder Empty")
                raise SystemExit("Folder Empty")

    def update_tags(self):
        bnw_path = join(getcwd(), "bnw_tags.txt")
        regular_path = join(getcwd(), "regular_tags.txt")
        if exists(bnw_path):
            with open(bnw_path, "r") as bnw:
                self.bnw_caption = ""
                for line in bnw.readlines():
                    self.bnw_caption += line
        if exists(regular_path):
            with open(regular_path, "r") as regular:
                self.regular_caption = ""
                for line in regular.readlines():
                    self.regular_caption += line

    def upload_photo(self):
        if 1 < dt.now().hour < 9 and self.bedtime:
            self.logger.log("Bed time, skipping upload")
            pass
        photo = self.photos.pop()
        caption = self.regular_caption
        if self.is_bnw(photo):
            caption += "\n\n" + self.bnw_caption
        try:
            with client(self.username, self.password) as cli:
                self.logger.log(photo)
                cli.upload(photo, caption)
            rename(photo, photo + ".UPLOADED")
        except IOError as e:
            if "The password you entered is incorrect." in str(e):
                self.config["credentials"]["password"] = ""
                with open(self.config_path, "w") as configfile:
                    self.config.write(configfile)
                raise WrongPassword("Password The password you entered is incorrect. Please try again.")
            else:
                self.photos.push(photo)
                self.logger.log("Retrying photo upload in 60 seconds.")
                sleep(60)
                self.upload_photo()
        except Exception as e:
            raise ServerError(e)

    def get_timeout(self):
        offset = choice([-1, 1]) * randrange(int(self.timeout / 20), int(self.timeout / 10) + 1)
        return self.timeout + offset

    def validate_mail_config(self):
        if "mailer" in self.config:
            if "to" in self.config["mailer"] and "username" in self.config["mailer"] and "password" in \
                    self.config["mailer"]:
                return True
        return False

    def send_email(self, nextupload):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Instagram Upload"
        msg['From'] = self.mail_username
        msg['To'] = self.mail_to
        html = """\
        <html>
          <head></head>
          <body>
            New photo uploaded on account <b><a href="https://instagram.com/{account}">{account}</a></b>.<br><br>
            Next scheduled for: <u><b>{nextupload}</u></b>.<br><br>
            Remaining photos: <b>{remaining}</b>.
          </body>
        </html>
        """.format(account=self.username, nextupload=nextupload, remaining=len(self.photos))
        text = (
                "Subject: Instagram Upload\n\nNew photo uploaded on account %s.\n\nNext scheduled for: %s.\nRemaining photos: %d." % (
            self.username, nextupload, len(self.photos)))
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.mail_username, self.mail_password)
        server.sendmail(self.mail_username, self.mail_to, msg.as_string())
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
        self.logger.log("Wrong password")


class ServerError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.logger.log("Server Error")


if __name__ == '__main__':
    Main()
