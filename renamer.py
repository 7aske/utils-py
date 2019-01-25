from os import getcwd, listdir, makedirs
from os.path import join, isdir, splitext, exists, isabs
from re import sub
from shutil import move, copy2
from sys import argv, stdout
from datetime import datetime as dtime
from pathlib import Path
import pyexiv2


class Main:
    root = ""
    source = ""
    photos = []
    data = {"TOTAL": 0}
    copy = False
    write = True
    scan = False
    default_source = "_INGEST"

    def __init__(self):
        if "--copy" in argv:
            self.copy = True
            argv.remove("--copy")
        if "--nowrite" in argv:
            self.write = False
            argv.remove("--nowrite")
        if "--scan" in argv:
            self.scan = True
            argv.remove("--scan")

        if "-f" in argv:
            try:
                path = argv[argv.index("-f") + 1]
                if isabs(path):
                    self.source = path
                else:
                    self.source = join(getcwd(), path)
            except Exception:
                raise SystemExit("-f [path]")
        else:
            self.source = join(getcwd(), self.default_source)

        if "-d" in argv:
            try:
                path = argv[argv.index("-d") + 1]
                if isabs(path):
                    self.root = join(getcwd(), path)
                else:
                    self.root = path
            except Exception:
                raise SystemExit("Usage: -d [path]")
        else:
            self.root = getcwd()

        if not exists(self.source):
            raise SystemExit("Invalid source folder")
        if not exists(self.root):
            raise SystemExit("Invalid destination folder")

        if not self.write:
            print("Result writing disabled")
        if self.scan:
            print("Started in scan mode")
            self.list_photos(self.root)
            self.scan_photos()
        else:
            print("Started in [%s] mode" % ("COPY" if self.copy else "MOVE"))
            print("Source:     \t" + self.source)
            print("Destination:\t" + self.root)
            answer = ""
            possible_answers = ["Y", "y", "N", "n"]

            while answer not in possible_answers:
                answer = input("Scan for photos? (Y/N) ")
            if answer.upper() == "Y":
                answer = ""
                self.list_photos(self.source)
                while answer not in possible_answers:
                    answer = input("%d photos found. Continue? (Y/N) " % len(self.photos))
                if answer.upper() == "Y":
                    self.rename_photos()
                else:
                    raise SystemExit("Bye")
            else:
                raise SystemExit("Bye")

    def list_photos(self, path):
        for entry in listdir(path):
            abs_path = join(path, entry)
            if isdir(abs_path):
                self.list_photos(abs_path)
            else:
                if abs_path.upper().endswith(".JPG") or abs_path.upper().endswith(".NEF") or abs_path.upper().endswith(
                        ".RAF"):
                    self.photos.append(abs_path)

    def scan_photos(self):
        for photo in self.photos:
            if self.source in photo:
                continue
            make, model, _, _, _ = self.get_exif(photo)

            if make in self.data.keys():
                if model in self.data[make].keys():
                    self.data[make][model] += 1
                else:
                    self.data[make][model] = 1
            else:
                self.data[make] = {model: 1}

            self.data["TOTAL"] += 1
            self.progress_bar(self.data["TOTAL"])

        print("\n" + str(self.data))
        if self.write:
            self.write_results()

    def rename_photos(self):
        for photo in self.photos:

            make, model, date, time, ext = self.get_exif(photo)

            file_name = "{date}_{time}_{model}{ext}".format(date=date, time=time, model=model, ext=ext.upper())
            folder_name = "{date}_{model}".format(date=date, model=model)
            folder_path = join(self.root, make, model, folder_name)
            file_path = join(folder_path, file_name)

            if not exists(folder_path):
                makedirs(folder_path)

            if self.copy:
                self.safe_copy(photo, file_path, 0)
            else:
                self.safe_move(photo, file_path, 0)

            if model in self.data.keys():
                self.data[model] += 1
            else:
                self.data[model] = 1
            self.data["TOTAL"] += 1
            self.progress_bar(self.data["TOTAL"])

        print("\n" + str(self.data))
        if self.write:
            self.write_results()

    @staticmethod
    def get_exif(photo):
        _, ext = splitext(photo)
        md = pyexiv2.ImageMetadata(photo)
        try:
            md.read()
        except Exception as e:
            raise SystemError(e)

        datetime = str(dtime.now())
        if "Exif.Photo.DateTimeDigitized" in md.exif_keys:
            datetime = str(md["Exif.Photo.DateTimeDigitized"].value)
        elif "Exif.Image.DateTime" in md.exif_keys:
            datetime = str(md["Exif.Image.DateTime"].value)

        make = "UNK-MAKE"
        model = "UNK-MODEL"
        if "Exif.Image.Make" in md.exif_keys:
            make = str(md["Exif.Image.Make"].value)
        if "Exif.Image.Model" in md.exif_keys:
            model = str(md["Exif.Image.Model"].value)
        if make == "NIKON-CORPORATION" or make == "SONY-ERICSSON":
            make = sub(r"-\w+", "", make)

        make = sub(r"[,.]", "", make)
        make = sub(r" ", "-", make).upper()
        model = sub(r" ", "-", model).upper()
        date = datetime.split(" ")[0]
        time = datetime.split(" ")[1]
        time = sub(r":", "-", time)

        if model == "FINEPIX-X100" or model == "COOLPIX-L5" or model == "NIKON-D3200" or model == "FINEPIX-X100S":
            model = sub(r"\w+-", "", model)
        elif model == "X-E1" or model == "MI-A1":
            model = sub(r"-", "", model)

        return make, model, date, time, ext

    def write_results(self):
        # path = join(str(Path.home()), "ingest_%s.txt" % str(dtime.now().date()).replace(" ", "", -1))
        if self.scan:
            path = "scan_%s.txt" % str(dtime.now().date()).replace(" ", "", -1)
        else:
            path = "ingest_%s.txt" % str(dtime.now().date()).replace(" ", "", -1)
        with open(path, "w") as f:
            for key in self.data.keys():
                value = self.data[key]
                if type(value) is dict:
                    f.write(key + ":\n")
                    for key2 in value.keys():
                        f.write("\t{key}: {value}\n".format(key=key2, value=value[key2]))
                else:
                    f.write("{key}: {value}\n".format(key=key, value=value))
                    if key == "TOTAL":
                        f.write("\n")
            f.close()

    def safe_move(self, photo, file_path, count):
        if not exists(file_path):
            try:
                move(photo, file_path)
            except Exception:
                raise SystemError("Error moving %s to %s" % photo, file_path)
        else:
            ext = file_path[-4:]
            if count == 0:
                new_path = file_path[:-4] + "-" + str(count) + ext
            else:
                pad = len(str(abs(count))) + 1
                new_path = file_path[:-4 - pad] + "-" + str(count) + ext
            count += 1
            self.safe_move(photo, new_path, count)

    def safe_copy(self, photo, file_path, count):
        if not exists(file_path):
            try:
                copy2(photo, file_path)
            except Exception:
                raise SystemError("Error copying %s to %s" % photo, file_path)
        else:
            ext = file_path[-4:]
            if count == 0:
                new_path = file_path[:-4] + "-" + str(count) + ext
            else:
                pad = len(str(abs(count))) + 1
                new_path = file_path[:-4 - pad] + "-" + str(count) + ext
            count += 1
            self.safe_copy(photo, new_path, count)

    def progress_bar(self, count):
        bar_len = 50
        total_len = len(self.photos)
        filled_len = int(round(bar_len * count / float(total_len)))
        status = total_len - count
        percents = round(100.0 * count / float(total_len), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        stdout.write('[%s] %.2f%s Files: %s \r' % (bar, percents, '%', status))
        stdout.flush()


if __name__ == "__main__":
    try:
        Main()
    except KeyboardInterrupt:
        print("\nBye")
