#! /bin/bash

rm -rf ./bin
mkdir bin/
javac -d bin/ `find ./com -name '*.java' -regex '^[./A-Za-z0-9]*$'`