#!/usr/bin/env python2

from bs4 import BeautifulSoup

import os
import urllib

BASE_LOC = 'http://poker.cs.ualberta.ca/IRCdata/'
DUMP_DIR = './archives/'
DOCUMENT = 'irc_poker_links.html'
PACKAGES = (
    "botsonly",
    "h1-nobots",
    "holdem",
    "holdemii",
    "holdem1",
    "holdem2",
    "holdem3",
    # "holdempot",
    # "nolimit",
)

def download(archive):
    print("Downloading {}".format(archive))
    urllib.urlretrieve(
        os.path.join(BASE_LOC, archive),
        os.path.join(DUMP_DIR, archive))

def main():
    with open(DOCUMENT) as links_doc:
        soup = BeautifulSoup(links_doc, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            href = link.get('href')
            link = None
            for p in PACKAGES:
                if href.startswith(p):
                    link = href
                    break
            if link is not None:
                download(link)

if __name__ == '__main__':
    main()
