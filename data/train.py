#!/usr/bin/env python

import sys
import pickle

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.naive_bayes import GaussianNB

from data import ACTIONCODES


class Training(object):
    def __init__(self, csv_file, training_set_pct=0.75):
        # create data frame containing your data, each column can be
        # accessed # by df['column   name']
        self.df = pd.read_csv(csv_file)

        # self.df['is_train'] = np.random.uniform(
        #     0, 1, len(self.df)) <= training_set_pct

        self.target_names = np.array(
            ['none',
             'blind',
             'fold',
             'check',
             'bet',
             'call',
             'raise',
             'allin',
             'quits',
             'kicked'])

        # columns you want to model
        self.target_col = self.df.columns[0]
        self.features_cols = self.df.columns[1:21]

        self.df['Targets'] = self.df[[self.target_col]]
        self.targets = np.array(self.df['Targets']).astype(int)

    def save_model(self, out='trained_model.pickle'):
        # Call Gaussian Naive Bayesian class with default parameters
        gnb = GaussianNB()
        gnb.fit(self.df[self.features_cols], self.targets)
        pickle.dump(gnb, open(out, 'wb'))


def main():
    t = Training(sys.argv[1])
    # import IPython; IPython.embed()
    t.save_model()

if __name__ == "__main__":
    main()
