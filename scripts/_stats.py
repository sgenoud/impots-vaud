"""Shared OLS trend-fit helper for the charges/subsides trend charts
(scripts/26, 27, 32): fit year vs. some per-capita/median-salary series,
get a 95% CI on the slope and the "is this a real trend" verdict used on
every trend chart's annotation and stdout report.
"""
from scipy import stats


def ols_fit(x, y):
    """OLS fit of y ~ x. Returns (fit, slope_lo, slope_hi, r_squared, verdict):
    fit is scipy's linregress result; slope_lo/slope_hi are the slope's
    95% CI via the t-distribution; verdict is the French one-line
    stability call (H0: slope = 0), based on fit.pvalue < 0.05."""
    fit = stats.linregress(x, y)
    n = len(x)
    t_crit = stats.t.ppf(0.975, n - 2)
    slope_lo, slope_hi = fit.slope - t_crit * fit.stderr, fit.slope + t_crit * fit.stderr
    r_squared = fit.rvalue ** 2
    verdict = "pas de tendance stable" if fit.pvalue < 0.05 else "compatible avec une tendance stable"
    return fit, slope_lo, slope_hi, r_squared, verdict
