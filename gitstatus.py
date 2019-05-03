#!/usr/bin/python3

from os import listdir, getcwd, environ, name
from os.path import isdir, join, isabs, basename
from subprocess import Popen, PIPE, call
from sys import argv

tasks = []
not_commited = 0
commited = 0
src = ""
flags = {
	"longlist": False,
	"list": False
}


def main():
	global src, flags
	if environ.get("CODE") is not "":
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
					if arg == "-l":
						flags["list"] = True
					elif arg == "-ll":
						flags["longlist"] = True

	call("clear") if name == "posix" else call("cls")
	check(src)


def check(p):
	global not_commited, commited, flags

	repo_structure = read_repos(p)
	repo_structure_noncommited = get_noncommited()

	if flags["longlist"]:
		print(verbose_structure(repo_structure, repo_structure_noncommited))
	else:
		if flags["list"]:
			print_nonverbose_structure_list(repo_structure, repo_structure_noncommited)
			print("{:14}{:14}\n".format(commited, "\033[31m\033[1;6;31m {}\033[00m".format(
			not_commited) if not_commited > 0 else ""))
		if not_commited > 0:
			print_nonverbose_structure(repo_structure_noncommited)
		else:
			print("\n\033[01;36mEverything up to date\033[00m")


def print_nonverbose_structure_list(struct, structnc):
	print("lang".ljust(12) + "#r" + "#n")
	print("".join(["-" for _ in range(24)]))
	for key in sorted(struct.keys()):
		print("\033[32m{}\033[00m".format(key.ljust(12)), "\033[33m{} \033[1;6;31m{}\033[00m".format(len(struct[key]), get_noncommited_len(structnc, key) if get_noncommited_len(structnc, key) > 0 else ""))


def print_nonverbose_structure(struct):
	for key in sorted(struct):
		for repo in struct[key]:
			print("\033[32m{}\033[00m".format(key.ljust(12)), "\033[33m{}\033[00m".format(repo))


def verbose_structure(struct, structnc):
	global src
	out = basename(src) + "\n"
	for n, key in enumerate(struct.keys()):

		last_lang = n == len(struct.keys()) - 1
		out += "{}──\033[1;32m{}\033[0;34m({}) \033[6;1;31m{}\033[00m\n".format("└" if last_lang else "├", key, len(struct[key]),
		                                                            get_noncommited_len(structnc,
		                                                                                key) if get_noncommited_len(
			                                                            structnc, key) > 0 else "")

		for i, repo in enumerate(struct[key]):
			last_repo = i == len(struct[key]) - 1
			# \033[31m{}\033[00m
			if key in structnc.keys() and repo in structnc[key]:
				out += "{}  {}──\033[31m{}*\033[00m\n".format(" " if last_lang else "│", "└" if last_repo else "├",
				                                              repo)
			else:
				out += "{}  {}──\033[33m{}\033[00m\n".format(" " if last_lang else "│", "└" if last_repo else "├", repo)
	return out


def get_noncommited_len(struct: dict, key: str):
	if key in struct.keys():
		return len(struct[key])
	else:
		return 0


def get_noncommited():
	global not_commited, commited
	out = {}
	for i, task in enumerate(tasks):
		output = str(task["task"].stdout.read())
		if not check_commited(output):
			lang = task["repo"][len(src):].split("/")[1]
			try:
				repo = task["repo"][len(src):].split("/")[2]
			except IndexError:
				repo = ""
			if lang not in out:
				out[lang] = [repo]
			else:
				out[lang].append(repo)
			not_commited += 1

		commited += 1
	return out


def read_repos(p: str):
	out = {}
	for rf in listdir(p):
		rf_abs = join(p, rf)

		if isdir(rf_abs) and not ignore(rf_abs) and not rf.startswith("_"):
			out[rf] = []
			if rf == ".git":
				add_to_tasks(p)
			elif ".git" in listdir(rf_abs):
				out[rf].append(rf)
				add_to_tasks(rf_abs)

			for gf in listdir(rf_abs):
				gf_abs = join(rf_abs, gf)
				if isdir(gf_abs):
					if ".git" in listdir(gf_abs):
						out[rf].append(gf)
						add_to_tasks(gf_abs)
	return out


def add_to_tasks(p: str):
	global tasks
	proc = Popen(["git", "-C", p, "status"], stderr=PIPE, stdout=PIPE)
	tasks.append({"task": proc, "repo": p})


def check_commited(output: str):
	errors = ["Changes to be committed", "Changes not staged for commit", "Untracked files"]
	for error in errors:
		if error in output:
			return False
	return True


def ignore(p: str):
	ignore_folders = ["_test", "_others"]
	if isdir(p):
		if basename(p) in ignore_folders:
			return True
	return False


if __name__ == "__main__":
	main()
