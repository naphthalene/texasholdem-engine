#!/usr/bin/env python2

import os
import re
import sys
import tarfile
import datetime
from operator import itemgetter
from itertools import izip_longest, chain

from sklearn import svm

# import IPython; IPython.embed()
DEBUG = False

ARCHIVES_DIR = './archives/'
PDB_MATCHER = re.compile(r'.+?\/.+?\/pdb\/pdb\..*')
SUITS = 'cdhs'
CARDS = '23456789TJQKA'
ACTIONCODES = '-BfkbcrAQK'

class Hand(object):
    def __init__(self, hand):
        parts = hand.split(None, 13)
        parts += [None] * (13 - len(parts))

        self.timestamp,\
        self.game_set,\
        self.game_number,\
        self.num_players,\
        self.flop,\
        self.turn,\
        self.river,\
        self.showdown,\
        self.flop_c1,\
        self.flop_c2,\
        self.flop_c3,\
        self.turn_c,\
        self.river_c = parts

        self.actionsets = []

    def encode_card(self, c):
        if c is None:
            return '0'
        return str(CARDS.index(c[0]) + 1 + SUITS.index(c[1]) * 13)

    def table_cards_encoded(self):
        return map(self.encode_card,
                   self.table_cards())


    def table_cards(self):
        return [self.flop_c1,
                self.flop_c2,
                self.flop_c3,
                self.turn_c,
                self.river_c]

    def __repr__(self):
        ret = '============='
        ret += ' [{}]\n'.format(self.timestamp)
        ret += 'Community\n'
        if any(map(lambda c: c is not None, [self.flop_c1,
                                             self.flop_c2,
                                             self.flop_c3])):
            ret += 'Flop: ({}) [{}]\n'.format(
                self.flop,
                ','.join(filter(None, [self.flop_c1,
                                       self.flop_c2,
                                       self.flop_c3])))
        if self.turn_c is not None:
            ret += 'Turn: ({}) [{}]\n'.format(
                self.turn,
                self.turn_c)
        if self.river_c is not None:
            ret += 'River: ({}) [{}]\n'.format(
                self.river,
                self.river_c)

        ret += 'Actions\n'
        ret += str(self.actionsets) + '\n'
        return ret


class ArchiveData(object):
    def __init__(self, tar, category, code):
        self.tar = tar
        self.category = category
        self.code = code
        self.ti_hdb = tar.getmember(os.path.join(category, code, 'hdb'))
        self.ti_hroster = tar.getmember(os.path.join(category, code, 'hroster'))
        self.ti_pdbs = []
        for member in tar.getmembers():
            if member.isfile() and PDB_MATCHER.match(member.name):
                self.ti_pdbs.append(member)

        self.hands = {}

        self.extract()

    def extract(self):
        """
        This function reads all of the files and builds an internal
        model of the games that it can emit as a sparse libsvm file for
        training
        """

        """
        HDB format
        ==========
        column 1        timestamp (supposed to be unique integer)
        column 2        game set # (incremented when column 3 resets)
        column 3        game # reported by dealer bot
        column 4        number of players dealt cards
        column 5        number of players who see the flop
        column 6        pot size at beginning of flop
        column 7        number of players who see the turn
        column 8        pot size at beginning of turn
        column 9        number of players who see the river
        column 10       pot size at beginning of river
        column 11       number of players who see the showdown
        column 12       pot size at showdown
        column 13+      cards on board (0, 3, 4 or 5)
        """

        # 1) Process HDB file first to obtain all of the hands played
        #    out
        for hand in self.tar.extractfile(self.ti_hdb).readlines():
            self.hands[hand.split()[0]] = Hand(hand)

        """
        HROSTER format
        ==============
        column 1        timestamp
        column 2        number of player dealt cards
        column 3+       player nicknames
        """

        # 2) Process HROSTER to determine who played each hand
        #    This can technically be inferred from the PDB files but
        #    what the heck
        # for roster in self.tar.extractfile(self.ti_hroster).readlines():
        #     # Split with a max of 12 for the timestamp, number of
        #     # players, and up to 10 possible players
        #     parts = roster.split(None, 12)
        #     parts += [None] * (12 - len(parts))
        #     for nick in parts[2:]:
        #         if nick is not None:
        #             self.hands[parts[0]].add_player(nick)

        """
        PDB format
        ==========
        column 1        player nickname
        column 2        timestamp of this hand (see HDB)
        column 3        number of player dealt cards
        column 4        position of player (starting at 1, in order of cards received)
        column 5        betting action preflop (see below)
        column 6        betting action on flop (see below)
        column 7        betting action on turn (see below)
        column 8        betting action on river (see below)
        column 9        player's bankroll at start of hand
        column 10       total action of player during hand
        column 11       amount of pot won by player
        column 12+      pocket cards of player (if revealed at showdown)
        """

        # 3) Process the PDB files
        for pdb in self.ti_pdbs:
            for l in self.tar.extractfile(pdb).readlines():
                actions = l.split()
                self.hands[actions[1]].actionsets.append(
                    (actions[3], actions[4:8]))
                # self.hands[actions[1]].players[actions[0]].add_actions(actions)

        # print self.hands.values()

    def emit_libsvm(self):
        flatten = lambda l: list(chain.from_iterable(l))
        encode = lambda a: ACTIONCODES.index(a)
        fill = lambda l,n,w: l + [w]*(n - len(l))

        for timestamp, hand in self.hands.iteritems():
            if DEBUG:
                print '------------------'
                print 'hand [{}] ({})'.format(
                    timestamp,
                    datetime.datetime.fromtimestamp(
                        int(timestamp)).strftime(
                            '%Y-%m-%d %H:%M:%S'))

                print '==TABLE CARDS=='
                print hand.table_cards()
                print hand.table_cards_encoded()


            # Sort by player seat
            actionsets = sorted(hand.actionsets, key=itemgetter(0))
            for player, actionset in actionsets:
                # Generate a row
                all_actions = flatten(map(list, map(list, actionset)))
                if DEBUG:
                    print all_actions

                if len(all_actions) > 15:
                    break

                for i, a in enumerate(all_actions):
                    if a == '-':
                        break
                    action = encode(a)
                    # acc.append(a)
                    action_part = \
                        [str(action)] +\
                        map(str,
                            fill(map(encode,
                                     all_actions[:i]), 15, 0))

                    print ', '.join(action_part + hand.table_cards_encoded())

            #     print "All actions: {}".format(
            #         list(chain(*izip_longest(*zip(
            #             *sorted(hand.actionsets,
            #                     key=itemgetter(0)))[1]))))


def process_archive(archive):
    archive_path = os.path.join(ARCHIVES_DIR, archive)
    category, code, _ = archive.split('.')
    tar = tarfile.open(archive_path, "r:gz")
    data = ArchiveData(tar, category, code)

    data.emit_libsvm()

def usage():
    print('''Please supply an archive name as an argument
    example: [./train.py botsonly.199810.tgz > data.csv]''')
    exit(1)

def main():
    if len(sys.argv) < 2:
        usage()

    process_archive(sys.argv[1])

if __name__ == "__main__":
    main()
