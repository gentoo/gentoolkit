Use the "runtests.sh" script to test the output of all commands in "cmds.txt"
against the output that the version of gentoolkit installed on the system
yields.

It's a great way to verify that a refactoring didn't affect output.

Usage:

$ cd cmdtests
$ ./runtests.sh

You can also test against a specific version of gentoolkit instead. Clone a
copy of gentoolkit to test against and then do:

$ cd cmdtests
$ ./runtests.sh /path/to/othergentoolkit/pym
