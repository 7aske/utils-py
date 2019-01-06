from os import getcwd, listdir, makedirs
from os.path import join, isdir, splitext, exists
from re import sub
from shutil import move
from sys import argv, stdout
from datetime import datetime as dtime
from pathlib import Path
import pyexiv2


class Main:
    root = getcwd()
    source = getcwd()
    cwd = getcwd()
    photos = []
    data = {"TOTAL": 0}

    def __init__(self):
        if len(argv) == 2:
            self.source = join(self.cwd, argv[1])
        else:
            self.source = join(self.cwd, "_INGEST")

        print("From:\t" + self.source)
        print("To:  \t" + self.root)
        answer = ""
        possible_answers = ["Y", "y", "N", "n"]
        while answer not in possible_answers:
            answer = input("Are you sure? (Y/N) ")
        if answer.upper() == "Y":
            answer = ""
            self.list_photos(self.source)
            print("%d photos found. Continue?" % len(self.photos))
            while answer not in possible_answers:
                answer = input("Are you sure? (Y/N) ")
            if answer.upper() == "Y":
                self.rename_photos()
            else:
                SystemExit("Bye")
        else:
            SystemExit("Bye")

    def list_photos(self, path):
        for entry in listdir(path):
            abs_path = join(path, entry)
            if isdir(abs_path):
                self.list_photos(abs_path)
            else:
                if abs_path.upper().endswith(".JPG") or abs_path.upper().endswith(".NEF") or abs_path.upper().endswith(
                        ".RAF"):
                    self.photos.append(abs_path)

    def rename_photos(self):
        for photo in self.photos:
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

            try:
                make = str(md["Exif.Image.Make"].value)
                model = str(md["Exif.Image.Model"].value)
            except KeyError as e:
                make = "UNK-MAKE"
                model = "UNK-MODEL"

            make = sub(r"[,.]", "", make)
            make = sub(r" ", "-", make).upper()
            model = sub(r" ", "-", model).upper()
            date = datetime.split(" ")[0]
            time = datetime.split(" ")[1]
            time = sub(r":", "-", time)

            if make == "NIKON-CORPORATION" or make == "SONY-ERICSSON":
                make = sub(r"-\w+", "", make)

            if model == "FINEPIX-X100" or model == "COOLPIX-L5" or model == "NIKON-D3200":
                model = sub(r"\w+-", "", model)
            elif model == "X-E1" or model == "MI-A1":
                model = sub(r"-", "", model)

            file_name = "{date}_{time}_{model}{ext}".format(date=date, time=time, model=model, ext=ext.upper())
            folder_name = "{date}_{model}".format(date=date, model=model)
            folder_path = join(self.root, make, model, folder_name)
            file_path = join(folder_path, file_name)

            try:
                makedirs(folder_path)
            except FileExistsError as e:
                pass

            self.safe_move(photo, file_path, 0)

            if model in self.data.keys():
                self.data[model] += 1
            else:
                self.data[model] = 1
            self.data["TOTAL"] += 1
            self.progress_bar(self.data["TOTAL"])

        print(self.data)
        self.save_results()

    def save_results(self):
        with open(join(str(Path.home()), "photos_%s.txt" % str(dtime.now().date()).replace(" ", "", -1)), "w") as f:
            for key in self.data.keys():
                f.write("{key}: {value}\n".format(key=key, value=self.data[key]))
            f.close()

    def safe_move(self, photo, file_path, count):
        if not exists(file_path):
            try:
                move(photo, file_path)
            except SystemError as e:
                raise SystemError(e)
        else:
            if count == 0:
                new_path = file_path[:-4] + str(count) + file_path[-4:]
            else:
                pad = len(str(abs(count)))
                new_path = file_path[:-4 - pad] + str(count) + file_path[-4:]
            count += 1
            self.safe_move(photo, new_path, count)

    def progress_bar(self, count):
        bar_len = 50
        total_len = self.data["TOTAL"]
        filled_len = int(round(bar_len * count / float(total_len)))
        status = total_len - count
        percents = round(100.0 * count / float(total_len), 2)
        bar = '#' * filled_len + '.' * (bar_len - filled_len)
        stdout.write('[%s] %.2f%s Files: %s \r' % (bar, percents, '%', status))
        stdout.flush()


if __name__ == "__main__":
    Main()
