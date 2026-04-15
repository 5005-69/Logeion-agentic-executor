#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./mygit.sh \"your commit message\""
    exit 1
fi

git add .
git commit -m "$1"
git push origin main
git status