"""
A module for portfolio optimization based on Entropic Drawdown at Risk
as detailed in this notebook

https://colab.research.google.com/github/cvxpy/cvxpy/blob/master/examples/notebooks/WWW/Entropic%20Portfolio.ipynb

Still an experimental object
"""
from typing import Dict
from typing import Optional
from typing import Tuple

import cvxpy as cp
import numpy as np
import pandas as pd
from pypfopt.exceptions import OptimizationError
from skportfolio.frontier._base_frontier import BaseConvexFrontier


class EfficientEDar(BaseConvexFrontier):
    """
    Base class for efficient entropic drawdown at risk
    """

    def __init__(
        self,
        expected_returns: pd.Series,
        returns: pd.DataFrame,
        alpha: float = 0.05,
        weight_bounds: Tuple[float, float] = (0, 1),
        solver: Optional[str] = None,
        verbose: bool = False,
        solver_options: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            n_assets=len(expected_returns),
            tickers=expected_returns.index.tolist(),
            weight_bounds=(0, 1),
            solver=solver,
            verbose=verbose,
            solver_options=solver_options,
        )
        self.expected_returns = self._validate_expected_returns(expected_returns)
        self.returns = self._validate_returns(returns)
        self.alpha = alpha
        self.weight_bounds = weight_bounds
        # needed in the creation of the efficient frontier
        self._max_return_value = None

    def min_edar(self):
        n_samples, n_assets = self.returns.shape

        w: cp.Variable = cp.Variable((n_assets, 1))

        t: cp.Variable = cp.Variable(shape=(1, 1))
        z: cp.Variable = cp.Variable(shape=(1, 1), nonneg=True)
        ui: cp.Variable = cp.Variable(shape=(1, 1))

        X = self.returns.dot(w)
        w_min, w_max = self.weight_bounds
        self._constraints = [
            cp.sum(ui) <= z,
            cp.constraints.ExpCone(-X - t, np.ones((n_samples, 1)) @ z, ui),
            cp.sum(w) == 1,
            w >= w_min,
            w <= w_max,
        ]
        self._objective = t + z * np.log(1 / (self.alpha * n_samples))

        self._opt = cp.Problem(
            objective=cp.Maximize(self._objective), constraints=self._constraints
        )
        try:
            self._opt.solve()
        except (TypeError, cp.DCPError) as current_exception:
            raise OptimizationError from current_exception

        if self._opt.status not in {"optimal", "optimal_inaccurate"}:
            raise OptimizationError("Solver status: {}".format(self._opt.status))

        self.weights = w.value
        return self._make_output_weights()
