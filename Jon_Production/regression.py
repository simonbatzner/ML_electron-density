#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, invalid-name, too-many-arguments

"""" Regression models

Simon Batzner
"""

import numpy as np

from scipy.optimize import minimize

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.model_selection import GridSearchCV
from sklearn.gaussian_process.kernels import RBF, Matern

from Jon_Production.utility import get_SE_K, GP_SE_alpha, minus_like_hyp, GP_SE_pred


class RegressionModel:
    """Base class for regression models"""

    def __init__(self, model, training_data, training_labels, test_data, test_labels, model_type, verbosity):
        """
        Initialization
        """
        self.model = model
        self.training_data = training_data
        self.training_labels = training_labels
        self.test_data = test_data
        self.test_labels = test_labels
        self.model_type = model_type
        self.verbosity = verbosity


class GaussianProcess(RegressionModel):
    """Gaussian Process Regression Model"""

    def __init__(self, training_data=None, training_labels=None, test_data=None, test_labels=None, kernel='rbf',
                 length_scale=1, length_scale_min=1e-5, length_scale_max=1e5, sigma=1, n_restarts=10,
                 verbosity=1, sklearn=False):
        """
        Initialization
        """
        self.length_scale = length_scale
        self.sklearn = sklearn
        self.verbosity = verbosity

        # predictions
        self.pred = None
        self.pred_var = None

        if self.sklearn:

            self.length_scale_min = length_scale_min
            self.length_scale_max = length_scale_max
            self.n_restarts = n_restarts

            self.kernel_dict = {'rbf': RBF(length_scale=self.length_scale,
                                           length_scale_bounds=(self.length_scale_min, self.length_scale_max)),
                                'matern_15': Matern(length_scale=self.length_scale,
                                                    length_scale_bounds=(self.length_scale_min, self.length_scale_max),
                                                    nu=1.5),
                                'matern_25': Matern(length_scale=self.length_scale,
                                                    length_scale_bounds=(self.length_scale_min, self.length_scale_max),
                                                    nu=2.5)}
            self.kernel = self.kernel_dict[kernel]
            self.model = GaussianProcessRegressor(kernel=self.kernel, n_restarts_optimizer=self.n_restarts)

        else:

            # PyFly implementation of a Gaussian Process
            self.model = None
            self.sigma = sigma
            self.K = None
            self.L = None
            self.alpha = None

        RegressionModel.__init__(self, model=self.model, training_data=training_data, test_data=test_data,
                                 training_labels=training_labels, test_labels=test_labels, model_type='gp',
                                 verbosity=verbosity)

    def opt_hyper(self):
        """
        Optimize hyperparameters by minimizing minus log likelihood w/ Nelder-Mead
        """
        args = (self.training_data, self.training_labels)

        # initial guess
        x0 = np.array([self.sigma, self.length_scale])

        # nelder-mead opt
        res = minimize(minus_like_hyp, x0, args, method='nelder-mead', options={'xtol': 1e-8, 'disp': True})

        self.sigma, self.length_scale = res.x[0], res.x[1]

    def train(self):
        """
        Train ML model on training_data/ training_labels
        """
        if self.sklearn:
            self.model.fit(self.training_data, self.training_labels)

        else:
            # optimize hyperparameters
            self.opt_hyper()

            # following: Algorithm 2.1 (pg. 19) of "Gaussian Processes for Machine Learning" by Rasmussen and Williams.
            self.K, self.L = get_SE_K(self.training_data, self.sigma, self.length_scale)

            # get alpha and likelihood
            self.alpha = GP_SE_alpha(self.K, self.L, self.training_data)

    def inference(self):
        """
        Predict on test data
        """

        if self.sklearn:
            # TODO: check this
            self.pred, std = self.model.predict(self.test_data, return_std=True)
            self.pred_var = std ** 2

        else:
            self.pred, self.pred_var = GP_SE_pred(self.training_data, self.training_labels, self.K,
                                                  self.L, self.alpha, self.sigma, self.length_scale, self.test_data)


class KernelRidgeRegression(RegressionModel):
    """KRR Regression Model"""

    def __init__(self, training_data, training_labels, test_data, test_labels, kernel,
                 alpha_range, gamma_range, cv, sklearn, verbosity):
        """
        Initialization
        """
        self.alpha_range = alpha_range
        self.gamma_range = gamma_range
        self.kernel = kernel
        self.verbosity = verbosity
        self.sklearn = sklearn
        self.cv = cv

        if self.sklearn:
            self.model = GridSearchCV(KernelRidge(kernel=self.kernel), cv=self.cv,
                                      param_grid={"alpha": self.alpha_range,
                                                  "gamma": self.gamma_range})

        else:
            # PyFly implementation of Kernel Ridge Regression
            pass

        RegressionModel.__init__(self, model=self.model, training_data=training_data, test_data=test_data,
                                 training_labels=training_labels, test_labels=test_labels, model_type='krr',
                                 verbosity=verbosity)

    def train(self):
        """
        Train ML model on training_data/ training_labels
        """
        self.model.fit(self.training_data, self.training_labels)

    def inference(self):
        """
        Predict on test data
        """
        self.model.predict(self.test_data)
