import smtplib
import ipaddress
from requests import get
from requests.exceptions import ConnectionError
from threading import Timer
from sys import argv


class Mailer():
    ip = ''
    username = '7aske.mailer.pi@gmail.com'
    password = ''
    to = 'ntasic7@gmail.com'

    def __init__(self):
        self.password = argv[1]
        self.ip = self.get_ip()
        self.check_ip_change()

    def get_ip(self):
        try:
            ip = get('https://api.ipify.org').text
        except ConnectionError:
            return self.ip
        return ip

    def check_ip_change(self):
        Timer(1800, self.check_ip_change).start()
        new_ip = self.get_ip()
        if new_ip != self.ip:
            self.ip = new_ip
            self.send_email(self.ip)

    def send_email(self, ip):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.username, self.password)
        server.sendmail(self.username, self.to, ip)
        server.quit()


if __name__ == "__main__":
    mailer = Mailer()
