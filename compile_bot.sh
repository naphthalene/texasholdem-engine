#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Please pass bot directory as argument."
  echo "./compile_bot.sh <bot_directory>"
  exit 1
fi

javac -d "$1"/bin/ `find $1 -name '*.java' -regex '^[./A-Za-z0-9]*$'`
