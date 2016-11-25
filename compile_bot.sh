#!/bin/bash

javac -d starterBot/bin/ `find starterBot -name '*.java' -regex '^[./A-Za-z0-9]*$'`
