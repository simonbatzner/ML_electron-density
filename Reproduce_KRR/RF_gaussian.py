#!/usr/bin/env python

"""" Random Forest KS - Mapping using Gaussian Potentials

    AP275 Class Project, Harvard University

    # References:
        [1] Brockherde et al. Bypassing the Kohn-Sham equations with machine learning. Nature Communications 8, 872 (2017)

Simon Batzner, Steven Torrisi, Jon Vandermause
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import os
from sklearn.datasets import load_boston
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import train_test_split
from KRR_reproduce import *


def load_data():
    print("Loading data...")
    ens = []
    seps = []
    fours = []

    for n in range(SIM_NO):
        # load separation, energy, and density
        sep = np.load(STR_PREF + 'sep_store/sep' + str(n) + '.npy')
        en = np.load(STR_PREF + 'en_store/en' + str(n) + '.npy')
        four = np.load(STR_PREF + 'four_store/four' + str(n) + '.npy')

        # put results in a nicer format
        sep = np.reshape(sep, (1,))[0]
        en = np.reshape(en, (1,))[0]['energy']
        four = np.real(four)

        # store quantities
        ens.append(en)
        seps.append(sep)
        fours.append(four)
    return ens, seps, fours


def main():
    seed = 42

    # params found from hyperparameter optimization
    n_estimators = 1000
    max_depth = 20
    test_size = 0.1
    grid_space = 0.8

    # load
    ens, seps, fours = load_data()

    # create gaussian potentials
    print("Building potentials...")
    pots = []
    grid_len = 5.29177 * 2

    for n in range(SIM_NO):
        dist = seps[n]
        pot = pot_rep(dist, grid_len, grid_space=grid_space)
        pot = pot.flatten()
        pots.append(pot)

    # setup training and test datas
    data = pots
    labels = ens
    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=test_size, random_state=seed)

    x_train = np.array(x_train)
    x_test = np.array(x_test)
    y_train = np.array(y_train)
    y_test = np.array(y_test)

    # train random forest
    estimator = RandomForestRegressor(random_state=seed, n_estimators=n_estimators, max_depth=max_depth)
    estimator.fit(x_train, y_train)

    # eval on training data
    y_true_train, y_pred_train = y_train, estimator.predict(x_train)

    # eval on test data
    y_true, y_pred = y_test, estimator.predict(x_test)

    print("\nNumber of estimators: {}".format(n_estimators))
    print("Maximum depth: {}".format(max_depth))
    print("\nMAE on training data: {}\n".format(mean_absolute_error(y_true_train, y_pred_train)))
    print("MAE on test data: {}".format(mean_absolute_error(y_true, y_pred)))


if __name__ == "__main__":
    global SIM_NO, STR_PREF, TEST

    SIM_NO = 150

    # path to data
g    os.environ['PROJDIR'] =  # project path
    STR_PREF = os.environ['PROJDIR'] +  # data

    main()
