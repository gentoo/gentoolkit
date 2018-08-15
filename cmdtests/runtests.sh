#!/bin/bash

TEST_AGAINST_PYTHON_PATH=$1

while read -r line; do
    echo "Running $line > before"
    PYTHONPATH="${TEST_AGAINST_PYTHON_PATH}"
    eval "$line" > before || exit 1
    echo "Running $line > after"
    PYTHONPATH="../pym"
    eval "$line" > after || exit 1
    DIFF=$(diff -u before after)
    if [[ -n $DIFF ]]; then
        echo "Different!"
        echo "$DIFF"
        exit 1
    fi
done < cmds.txt

rm before after
echo "All commands output the exact same thing!"
