#!/usr/bin/python3

from os import listdir, getcwd, environ
from os.path import isdir, join, exists, isabs, basename
from subprocess import Popen, PIPE
import configparser
from pathlib import Path
from sys import argv

repo_list = []
proc_list = []
langs = {}
config = configparser.ConfigParser()
config_path = join(getcwd(), "gitstatus.ini")
config_path_home = join(str(Path.home()), "gitstatus.ini")
not_commited = 0
commited = 0
src = ""


def check(p):
	global not_commited, commited
	for rf in listdir(p):
		rf_abs = join(p, rf)

		if isdir(rf_abs) and not ignore(rf_abs):
			langs[rf] = 0
			if rf == ".git":
				git_status(p)
			elif ".git" in listdir(rf_abs):
				langs[rf] += 1
				git_status(rf_abs)

			for gf in listdir(rf_abs):
				gf_abs = join(rf_abs, gf)
				if isdir(gf_abs):
					if ".git" in listdir(gf_abs):
						langs[rf] += 1
						git_status(gf_abs)

	test = {}

	print("Language".ljust(12) + "No")
	print("".join(["-" for _ in range(14)]))

	for i in sorted(langs):
		print(i.ljust(12), langs[i])

	print("\nNot commited:")

	for i, p in enumerate(proc_list):
		out = str(p.stdout.read())
		if not check_commited(out):
			lang = repo_list[i][len(src):].split("/")[1]
			try:
				repo = repo_list[i][len(src):].split("/")[2]
			except IndexError:
				repo = ""
			if lang not in test:
				test[lang] = [repo]
			else:
				test[lang].append(repo)

			not_commited += 1

		commited += 1

	out = basename(src) + "\n"
	for n, key in enumerate(test.keys()):

		last_lang = n == len(test.keys()) - 1
		out += "{}──{}\n".format("└" if last_lang else "├", key)

		for i, repo in enumerate(test[key]):

			last_repo = i == len(test[key]) - 1
			out += "{}  {}──{}\n".format(" " if last_lang else "│", "└" if last_repo else "├", repo)

	print(out)
	print("Checked: {} | Not commited: {}".format(commited, not_commited))


def git_status(p: str):
	repo_list.append(p)
	proc = Popen(["git", "-C", p, "status"], stderr=PIPE, stdout=PIPE)
	proc_list.append(proc)


def check_commited(output: str):
	errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
	for error in errors:
		if error in output:
			return False
	return True


def ignore(p):
	ignore_folders = ["_test", "_others"]
	if isdir(p):
		if basename(p) in ignore_folders:
			return True
	return False


if exists(config_path):
	config.read(config_path)
	src = config["path"]["src"]
elif exists(config_path_home):
	config.read(config_path_home)
	src = config["path"]["src"]
elif environ.get("CODE") is not "":
	src = environ.get("CODE")
else:
	raise SystemExit("Usage:\n\tsetup env variable 'CODE'\n\twith the path of the folder you want to check")

if len(argv) == 2:
	path = argv[1]
	if isabs(path):
		src = path
	elif path in listdir(src):
		src = join(src, argv[1])
	else:
		src = join(getcwd(), path)

Popen("clear")
print("Path: " + src)
check(src)
