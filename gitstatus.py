#!/usr/bin/python3

from os import listdir, getcwd, environ, name
from os.path import isdir, join, exists, isabs, basename
from subprocess import Popen, PIPE, call
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
verbose = False


def check(p):
	global not_commited, commited
	for rf in listdir(p):
		rf_abs = join(p, rf)

		if isdir(rf_abs) and not ignore(rf_abs) and not rf.startswith("_"):
			langs[rf] = []
			if rf == ".git":
				git_status(p)
			elif ".git" in listdir(rf_abs):
				langs[rf].append(rf)
				git_status(rf_abs)

			for gf in listdir(rf_abs):
				gf_abs = join(rf_abs, gf)
				if isdir(gf_abs):
					if ".git" in listdir(gf_abs):
						langs[rf].append(gf)
						git_status(gf_abs)

	langsn = {}
	for i, p in enumerate(proc_list):
		out = str(p.stdout.read())
		if not check_commited(out):
			lang = repo_list[i][len(src):].split("/")[1]
			try:
				repo = repo_list[i][len(src):].split("/")[2]
			except IndexError:
				repo = ""
			if lang not in langsn:
				langsn[lang] = [repo]
			else:
				langsn[lang].append(repo)

			not_commited += 1

		commited += 1

	if verbose:
		out = basename(src) + "\n"
		for n, key in enumerate(langs.keys()):

			last_lang = n == len(langs.keys()) - 1
			out += "{}──\033[32m{}\033[00m ({})\n".format("└" if last_lang else "├", key, len(langs[key]))

			for i, repo in enumerate(langs[key]):
				last_repo = i == len(langs[key]) - 1
				# \033[31m{}\033[00m
				if key in langsn.keys() and repo in langsn[key]:
					out += "{}  {}──\033[31m{}*\033[00m\n".format(" " if last_lang else "│", "└" if last_repo else "├", repo)
				else:
					out += "{}  {}──\033[33m{}\033[00m\n".format(" " if last_lang else "│", "└" if last_repo else "├", repo)
		print(out)
	else:
		print("Language".ljust(12) + "No")
		print("".join(["-" for _ in range(14)]))
		for i in sorted(langs):
			print("\033[32m{}\033[00m".format(i.ljust(12)), "\033[33m{}\033[00m".format(len(langs[i])))

		if not_commited > 0:
			print("\n\033[31mNot commited:\033[00m")
			out = basename(src) + "\n"
			for n, key in enumerate(langsn.keys()):

				last_lang = n == len(langsn.keys()) - 1
				out += "{}──\033[32m{}\033[00m\n".format("└" if last_lang else "├", key)

				for i, repo in enumerate(langsn[key]):
					last_repo = i == len(langsn[key]) - 1
					out += "{}  {}──\033[33m{}\033[00m\n".format(" " if last_lang else "│", "└" if last_repo else "├", repo)
			print(out)
		else:
			print("\n\033[01;36mEverything up to date\033[00m")

	print("Checked: {}{}".format(commited, " | \033[31mNot commited: \033[5;7;31m{}\033[00m".format(not_commited) if not_commited > 0 else 0))


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
if len(argv) > 1:
	for i, arg in enumerate(argv):
		if i >= 1:
			if not arg.startswith("-"):
				if isabs(arg):
					src = arg
				elif arg in listdir(src):
					src = join(src, arg)
				else:
					src = join(getcwd(), arg)
			else:
				if arg == "-v":
					verbose = True

call("clear") if name == "posix" else call("cls")
check(src)
