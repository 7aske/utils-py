import smtplib
from requests import get
from requests.exceptions import ConnectionError
from threading import Timer
from sys import argv, platform
from time import strftime, gmtime
from getpass import unix_getpass, win_getpass


class Mailer():
    ip = ''
    username = '7aske.mailer.pi@gmail.com'
    password = ''
    to = 'ntasic7@gmail.com'
    delay = 60

    def __init__(self):
        if len(argv) == 2:
            self.delay = int(argv[1])

        self.password = unix_getpass("Enter password: ") if platform == "linux" else win_getpass("Enter password: ")
        self.ip = self.get_ip()
        self.check_ip_change()

    def get_ip(self):
        try:
            ip = get('https://api.ipify.org').text
        except ConnectionError:
            return self.ip
        return ip

    def check_ip_change(self):
        timer = Timer(self.delay, self.check_ip_change)
        timer.start()
        new_ip = self.get_ip()
        time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print("IP:%s\nTime:%s" % (new_ip, time))
        if new_ip != self.ip:
            self.ip = new_ip
            self.send_email(self.ip, time)

    def send_email(self, ip, time):
        text = "New IP address is: %s\nTime of change: %s" % (ip, time)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.username, self.password)
        server.sendmail(self.username, self.to, text)
        server.quit()
        print("Mail sent")


if __name__ == "__main__":
    Mailer()
