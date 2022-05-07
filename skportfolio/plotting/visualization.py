import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skportfolio.frontier._efficientfrontier import (
    _BaseEfficientFrontierPortfolioEstimator,
)


def _validate_plotting_kwargs(**kwargs):
    valid_kwargs = [
        "figsize",
        "title",
        "fontsize",
        "legend_loc",
        "asset_color",
        "risk_return_color",
        "risk_return_line_width",
        "risk_return_line_style",
        "show_only_portfolio",
        "frontier_line_color",
        "show_tangency_line",
        "autoset_lims",
    ]
    for k, v in kwargs.items():
        if k not in valid_kwargs:
            raise ValueError(
                f"Non supported kwarg {k}. Supported list is\n{','.join(valid_kwargs)}"
            )


def plot_frontier(
    ptf_estimator: _BaseEfficientFrontierPortfolioEstimator,
    prices_or_returns,
    num_portfolios: int = 20,
    show_assets=False,
    ax=None,
    **kwargs,
):
    """
    Plot the efficient frontier for the base class this portfolio method belongs to.
    If the portfolio has already been fit to data, it additionally plots a dot showing where it belongs along
    the efficient risk-return frontier.

    Parameters
    ----------
    ptf_estimator :_BaseEfficientFrontierPortfolioEstimator
        An instantiated portfolio object inheriting from _BaseEfficientFrontierPortfolioEstimator
        This requirement is because other miscellaneous portfolio methods don't have the `estimate_frontier`
        method used to calculate all (risk,reward) coordinates.
    prices_or_returns: pd.DataFrame
        Asset prices or returns
    num_portfolios: int
        Number of points along the efficient frontier
    show_assets: bool
        Whether to additionally display dots representing portfolios made uniquely by each single asset.
    ax: matplotlib axis object
        If None a new axis is created, otherwise plotting is done on the provided axis

    Other Parameters
    ----------------
    **kwargs:
        Additional keyworkds for figure aesthetic control. They are the following:

        - figsize: None
            Figure size as a pair (width, height)
        - title: str
            Title of the figure. Default 'Efficient frontier'
        - fontsize: int
            Size of the labels. Default 8.
        - legend_loc: int
            Position of the legend. Default 2 (upper left).
        - asset_color: str
            Color of the individual assets over the efficient frontier. Default 'darkgrey'
        - risk_return_color: str
            Color of the fitted portfolio dot and lines. Default set to "C0" the first color
            in the color cycle.
        - risk_return_line_width: int
            Width of the risk-return vertical and horizontal lines. Default 1
        - risk_return_line_style: str
            Line style of the risk-return vertical and horizontal lines. Default dashed '--'.
        - show_only_portfolio: bool
            Whether to only show the portfolio location, without the entire frontier. Used when plotting
            multiple portfolios over the frontier. Default False, it draws the entire frontier.
        - frontier_line_color: str
            Color of the plot of the efficient frontier. Default None
        - show_tangency_line: bool
            Show the tangency line that has for 0 volatility the value of risk_free_rate
        - autoset_lims: bool
            Whethet to automatically set the axes x-y limits. Default True

    Returns
    -------
    object
    matplotlib axis object containing the picture
    """
    _validate_plotting_kwargs(**kwargs)

    if ax is None:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=kwargs.get("figsize", None))
        except ImportError as importerror:
            raise importerror

    if not kwargs.get("show_only_portfolio", False):
        risks, returns, frontier_weights = ptf_estimator.estimate_frontier(
            X=prices_or_returns, num_portfolios=num_portfolios
        )
        ax.plot(
            risks,
            returns,
            "-",
            color=kwargs.get("frontier_line_color", "C0"),
            label=str(ptf_estimator),
        )

    ax.set_ylabel("Portfolio return")
    ax.set_xlabel(
        ptf_estimator._min_risk_method_name.replace("min_", "")
        .replace("_", " ")
        .title()
    )
    ax.set_title(kwargs.get("title", "Efficient frontier"))
    ax.grid(which="both")

    # if true, it builds temporaneous asset price or returns dataframes with each single asset.
    # The riskiest asset always lies at the highest risk/highest return because of the properties of the efficient
    # frontier, whereas minimum risk is always at the minimum return along the frontier.
    if not (isinstance(show_assets, bool) or isinstance(show_assets, list)):
        raise TypeError("show_assets can be either a boolean or list of assets to show")
    if show_assets is True:
        show_assets = prices_or_returns.columns.tolist()
    elif show_assets is False:
        show_assets = []
    for asset in show_assets:
        # model made of one single asset
        model_asset = ptf_estimator._optimizer(prices_or_returns[[asset]])
        # fit the asset_return = max return portfolio
        model_asset._max_return()
        asset_risk, asset_return = ptf_estimator.risk_reward(model_asset)
        ax.scatter(
            x=[asset_risk],
            y=[asset_return],
            color=kwargs.get("asset_color", "darkgrey"),
        )
        ax.annotate(
            xy=(asset_risk, asset_return),
            text=asset,
            fontsize=kwargs.get("fontsize", 8),
        )

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    if ptf_estimator.model is not None:

        x, y = ptf_estimator.risk_reward()
        ax.scatter(
            x,
            y,
            color=kwargs.get("risk_return_color", "C0"),
        )
        ax.plot(
            (x, x),
            (ax.get_ylim()[0], y),
            color=kwargs.get("risk_return_color", "C0"),
            linestyle=kwargs.get("risk_return_line_style", "--"),
            linewidth=kwargs.get("risk_return_line_width", 1),
        )
        ax.plot(
            (ax.get_xlim()[0], x),
            (y, y),
            color=kwargs.get("risk_return_color", "C0"),
            linestyle=kwargs.get("risk_return_line_style", "--"),
            linewidth=kwargs.get("risk_return_line_width", 1),
        )
        if "show_tangency_line" in kwargs and hasattr(ptf_estimator, "risk_free_rate"):
            ax.plot((0, x), (ptf_estimator.risk_free_rate, y), "k--", linewidth=0.8)
        if kwargs.get("autoset_lims", True):
            ax.set_xlim([xmin, xmax])
            ax.set_ylim([ymin, ymax])
    ax.legend(loc=kwargs.get("legend_loc", 2))
    return ax


def pie_chart(weights: pd.Series, threshold: int = 12, ax=None, **kwargs):
    if ax is None:
        fig, ax = plt.subplots(figsize=kwargs.pop("figsize", (7, 7)))
    n_weights = weights.shape[0]
    weights = weights.sort_values(ascending=False)
    weights_thr = weights.head(threshold)
    weights_thr = pd.concat(
        [
            weights_thr,
            pd.Series(index=["Other"], data=weights.tail(n_weights - threshold).sum()),
        ],
        axis=0,
    )
    weights_thr = weights_thr.sample(
        frac=1
    )  # to shuffle the weights and avoid concentration in plot
    wedges, texts = ax.pie(weights_thr, wedgeprops=dict(width=0.5), startangle=-40)

    bbox_props = dict(
        boxstyle="square,pad=0.3",
        fc=kwargs.pop("backgroundcolor", None),
        ec=kwargs.pop("linecolor", None),
        lw=kwargs.pop("linewidth", 0.72),
    )
    kw = dict(arrowprops=dict(arrowstyle="-"), bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1) / 2.0 + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update(
            {
                "connectionstyle": connectionstyle,
                "color": kwargs.pop("linecolor", f"C{i}"),
            }
        )
        ax.annotate(
            f"{weights_thr.index[i]}: {(100*weights_thr.iloc[i]):.1f}%",
            xy=(x, y),
            xytext=(1.35 * np.sign(x), 1.4 * y),
            horizontalalignment=horizontalalignment,
            **{**kw, **kwargs},
        )

    ax.set_title(f"{weights.name}", y=1.15)
    return ax
