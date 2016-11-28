#!/usr/bin/env python2

import os
import re
import sys
import tarfile

from sklearn import svm

ARCHIVES_DIR = './archives/'
PDB_MATCHER = re.compile(r'.+?\/.+?\/pdb\/pdb\..*')

# class Action(object):
#     def __init__(self, ):

#     def add_actions(self, a):
#         # import IPython; IPython.embed()
#         self.actions[a[1]] = a[4:8]

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

        self.actions = []

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
        ret += str(self.actions) + '\n'
        return ret

    # def add_player(self, player_nick):
    #     """
    #     Adds a new player to the dictionary
    #     """
    #     assert(len(self.players.keys()) + 1 < self.num_players)
    #     if player_nick not in self.players.keys():
    #         self.players[player_nick] = []


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
                self.hands[actions[1]].actions.append(actions[4:8])
                # self.hands[actions[1]].players[actions[0]].add_actions(actions)

        # print self.hands.values()

    def emit_libsvm(self):
        for _, hand in self.hands.iteritems():
            for actionset in hand.actions:
                for i, action in enumerate(actionset):
                    if action == '-':
                        continue
                    if i == 0:
                        continue
                    print i, action

        return 'Not yet'


# class PDB(object):
#     def __init__(self, pdb_contents):
#         self.pdb_contents = pdb_contents

def process_archive(archive):
    archive_path = os.path.join(ARCHIVES_DIR, archive)
    category, code, _ = archive.split('.')
    tar = tarfile.open(archive_path, "r:gz")
    data = ArchiveData(tar, category, code)

    print data.emit_libsvm()

def usage():
    print('''Please supply an archive name as an argument
example: [./train.py botsonly.199810.tgz]''')
    exit(1)

def main():
    if len(sys.argv) < 2:
        usage()

    process_archive(sys.argv[1])

if __name__ == "__main__":
    main()
