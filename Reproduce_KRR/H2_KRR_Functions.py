# KRR H2 helper functions
import os
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from KRR_reproduce import *
from H2_KRR_Functions import *
from generate_H2_data import *
from scipy.interpolate import interp1d
import time
import numpy as np
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import learning_curve
from sklearn.kernel_ridge import KernelRidge
import matplotlib.pyplot as plt
rng = np.random.RandomState(0)

def get_train_test(M, N, seps, ens, fours):
    # define training and test indices
    train_indices = [int(n) for n in np.round(np.linspace(0,N-1,M))]
    test_indices = [n for n in range(N) if n not in train_indices]

    # define train and test sets
    train_set = np.reshape(np.array([seps[n] for n in train_indices]),(M,1))
    test_set = np.reshape(np.array([seps[n] for n in test_indices]),(N-M,1))

    train_ens = np.reshape(np.array([ens[n] for n in train_indices]),(M,1))
    test_ens = np.reshape(np.array([ens[n] for n in test_indices]),(N-M,1))

    train_fours = np.array([fours[n] for n in train_indices])
    test_fours = np.array([fours[n] for n in test_indices])
    
    return  train_set, test_set, train_ens, test_ens, train_fours, test_fours

def fit_krr(train_X, train_Y, test_X, test_Y, alphas, gammas, cv):
    # define model
    kr = GridSearchCV(KernelRidge(kernel='rbf'), cv=cv,
                      param_grid={"alpha": alphas,
                                  "gamma": gammas})
    
    # fit model
    kr.fit(train_X, train_Y)
    
    # predict test energies
    y_kr = kr.predict(test_X)
    
    # calculate MAE and max error
    errs = np.abs(test_Y-y_kr)
    MAE = np.mean(np.abs(test_Y-y_kr))
    max_err = np.max(np.abs(test_Y-y_kr))
    
    return kr, y_kr, errs, MAE, max_err

def fit_quick(train_X, train_Y, alpha, gamma):
    kr = KernelRidge(kernel='rbf',alpha = alpha, gamma = gamma)
    kr.fit(train_X, train_Y)
    return kr

def fit_KS(train_set, train_ens, test_set, test_ens, alphas, gammas, cv, seps, ens):
    [kr, y_kr, errs, MAE, max_err] = fit_krr(train_set, \
                                         train_ens, test_set, test_ens, \
                                         alphas, gammas, cv)
    
    # check MAE in kcal/mol
    print(kr.best_estimator_)

    # plot predictions
    plt.figure()
    plt.plot(train_set, train_ens, 'x')
    plt.plot(seps, ens, 'b')
    plt.plot(test_set, y_kr,'r')
    plt.show()

    # plot error
    fig, ax = plt.subplots(1,1)
    ax.plot(test_set, errs,label='KS')
    ax.set_xlabel('separation (Å)')
    ax.set_ylabel('log error')
    ax.set_yscale('log')
    plt.legend()
    plt.show()
    
    return kr, y_kr, errs, MAE, max_err

def fit_KS_pot(train_set, train_ens, test_set, test_ens, alphas, gammas, cv, seps):
    [kr, y_kr, errs, MAE, max_err] = fit_krr(train_set, \
                                         train_ens, test_set, test_ens, \
                                         alphas, gammas, cv)
    
    # check MAE in kcal/mol
    print(kr.best_estimator_)
    
    return kr, y_kr, errs, MAE, max_err

def spline_test(train_set, train_ens, test_set, test_ens):
    f = interp1d(train_set.reshape(len(train_set),), \
                  train_ens.reshape(len(train_ens),), kind='cubic')
    
    errs = f(test_set)-test_ens
    err = np.mean(np.abs(f(test_set)-test_ens))
    
    return err, errs

def get_potentials(train_set, M, grid_len = 5.29177*2):
    # get potential kernel
    pots = []
    for n in range(M):
        dist = train_set[n]
        pot = pot_rep(dist, grid_len)
        pots.append(pot) 
        
    pots = np.array(pots)
    pots = np.reshape(pots,(M, pots.shape[1]**3))
    
    return pots

def pos_to_four(train_set, train_fours, M, alpha, gamma):
    # build position to Fourier models
    krs = []
    no_four = 25
    train_X = np.reshape(train_set, (M,1))

    alpha = 1e-10
    gamma = 1

    for i in range(no_four):
        four1 = i
        for j in range(no_four):
            four2 = j
            for k in range(no_four):
                four3 = k
                
                # build model
                train_Y = np.reshape(train_fours[:,four1, four2, four3],(M,1))
                kr = fit_quick(train_X, train_Y, alpha, gamma)

                krs.append(kr)    
    return krs

def four_to_en(train_fours, train_ens, M, N, seps, test_fours, test_ens):
    # build Fourier to energy model
    train_X = np.reshape(train_fours,(M,25**3))
    test_X = np.reshape(test_fours,(N-M,25**3))
    train_Y = train_ens

    alphas = np.logspace(-20, -1, 6)
    gammas = np.logspace(-9, -7, 100)
    
    if M < 10:
        cv = M - 1
    else:
        cv = 9

    [FE_kr, y_kr, errs, MAE, max_err] = fit_krr(train_X, \
                                             train_Y, test_X, test_ens, \
                                             alphas, gammas, cv)
    
    return FE_kr, y_kr, errs, MAE, max_err

def doub_map_fast(test_set, test_ens, krs, FE_kr, pred_dim):
    # perform double mapping
    no_four = 25

    # get density
    test_dens = np.zeros([pred_dim, no_four, no_four, no_four])
    count = 0
    for i in range(no_four):
        for j in range(no_four):
            for k in range(no_four):
                # use model to calculate density
                kr_curr = krs[count]
                test_dens[:,i,j,k]=kr_curr.predict(test_set).reshape(-1,)

                count+=1

    # get energy
    pred_ens = FE_kr.predict(np.reshape(test_dens,(pred_dim,25**3)))
    HK_errs = test_ens-pred_ens
    MAE = np.mean(np.abs(HK_errs))
    max_err = np.max(np.abs(HK_errs))
    
    return HK_errs, MAE, max_err, pred_ens