#!/usr/bin/env python

import sys
import os
from glob import glob
import subprocess

def main():
    with open('training_data.csv', 'w') as outfile:
        for category in ['holdem']:
            for archive in glob('./archives/{}.*'.format(category)):
                print archive.split('/')[-1]
                subprocess.call(
                    ['python',
                     'data.py',
                     archive.split('/')[-1]],
                    stdout=outfile)

if __name__ == "__main__":
    main()
