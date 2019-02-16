import smtplib
from pathlib import Path
from requests import get
from requests.exceptions import ConnectionError
from sys import argv, platform
from time import strftime, gmtime, sleep
import configparser
import getpass
from os import system, getcwd, path
from os.path import join, exists


class Logger:
    filename = ""
    out = True

    def __init__(self, filename="ipmailer.log"):
        self.filename = path.join(str(Path.home()), filename)

    def log(self, data):
        if self.out:
            with open(self.filename, "a+") as f:
                f.write(data.replace("\n", " ") + "\n")
        print(data)

    def setout(self, out):
        self.out = out

    def getout(self):
        return self.out


class Mailer:
    username = ""
    password = ""
    send_to = ""
    noip_username = ""
    noip_password = ""
    noip_hostname = ""
    ip = ""
    delay = 60
    config = configparser.ConfigParser()
    config_path = join(getcwd(), "ipmailer.ini")
    logger = None

    def __init__(self):
        self.logger = Logger()
        if "-t" in argv:
            try:
                self.delay = int(argv[argv.index("-t") + 1])
                self.logger.log("Delay set to " + str(self.delay))
            except ValueError:
                self.delay = 60
                self.logger.log("Invalid timer value, defaulting to 60s")

        if "--log" not in argv:
            self.logger.setout(False)

        if exists(self.config_path):
            self.config.read(self.config_path)
            if not self.validate_config():
                raise SystemExit("Bad config")
        else:
            self.update_config()

        while True:
            self.ip = self.get_ip()
            self.check_ip_change()
            sleep(self.delay)

    def get_ip(self):
        try:
            ip = get("https://api.ipify.org").text
        except ConnectionError:
            return self.ip
        return ip

    def check_ip_change(self):
        new_ip = self.get_ip()
        time = strftime("%m-%d %H:%M:%S", gmtime())
        self.logger.log("{time} - {ip}".format(time=time, ip=new_ip))
        if new_ip != self.ip:
            self.ip = new_ip
            self.send_email(self.ip, time)
            self.update_dns()

    def send_email(self, ip, time):
        text = "New IP address is: %s\nTime of change: %s" % (ip, time)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.username, self.password)
        server.sendmail(self.username, self.send_to, text)
        server.quit()
        self.logger.log("{} - Mail sent".format(time))

    def update_dns(self):
        time = strftime("%m-%d %H:%M:%S", gmtime())
        update_cmd = "noipy -u " + self.noip_username + " -p " + self.noip_password + " -n " + self.noip_hostname + " --provider noip"
        out = system(update_cmd)
        self.logger.log("{} - DNS Updated".format(time))

    def validate_config(self):
        if "noip" not in self.config or "nodemailer" not in self.config:
            return False
        elif "username" not in self.config["noip"] or "password" not in self.config["noip"] or "hostname" not in \
                self.config["noip"]:
            return False
        elif "username" not in self.config["nodemailer"] or "password" not in self.config[
            "nodemailer"] or "send_to" not in self.config["nodemailer"]:
            return False
        else:
            return True

    def update_config(self):
        self.username = input("Mailer username: ")
        self.password = getpass.unix_getpass("Enter password: ") if platform == "linux" else getpass.win_getpass(
            "Enter password: ")
        self.send_to = input("Send to e-mail: ")
        self.noip_username = input("No-ip username: ")
        self.noip_password = getpass.unix_getpass(
            "Enter No-ip password: ") if platform == "linux" else getpass.win_getpass(
            "Enter No-ip password: ")
        self.noip_hostname = input("No-ip hostname: ")
        self.config["nodemailer"] = {
            "username": self.username,
            "password": self.password,
            "send_to": self.send_to
        }
        self.config["noip"] = {
            "username": self.noip_username,
            "password": self.noip_password,
            "hostname": self.noip_hostname
        }
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)
            configfile.close()


if __name__ == "__main__":
    try:
        Mailer()
    except KeyboardInterrupt:
        pass
