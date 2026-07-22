"""
隐藏评分测试(出题方保留, 不给被测 Agent)。
1. target:       加权方差以加权均值为中心(核心 bug)。
2. completeness: 加权半方差(semi_variance)作为同源函数, 其默认中心应与 variance 一致
   (related-behavior)  —— 检验 Agent 是否一并修正了同源的 semi_variance, 而非只改 variance、
                          或对 test_public_reproduction 的特定输入硬编码。
3. regression:   无 sample_weight 时, variance 行为不变(等于 np.var, ddof=1)。
"""
import numpy as np
from skfolio.measures import variance, semi_variance


def _data():
    r = np.array([0.015, -0.03, 0.02, -0.005, 0.04, -0.01])
    w = np.array([0.30, 0.25, 0.20, 0.10, 0.10, 0.05])
    return r, w / w.sum()


def test_target_weighted_variance_centered_on_weighted_mean():
    r, w = _data()
    got = variance(r, sample_weight=w, biased=True)
    wmean = np.sum(w * r)
    expected = np.sum(w * (r - wmean) ** 2)
    assert np.isclose(got, expected)


def test_completeness_weighted_semivariance_related_behavior():
    """related-behavior: 半方差默认阈值(min_acceptable_return)应与 variance 采用一致的加权中心。"""
    r, w = _data()
    got = semi_variance(r, sample_weight=w, biased=True)
    wmean = np.sum(w * r)
    expected = np.sum(w * np.maximum(0, wmean - r) ** 2)
    assert np.isclose(got, expected)


def test_regression_unweighted_variance_unchanged():
    """无权重时 variance 应仍等于 numpy 无偏方差(ddof=1)。"""
    r = np.array([0.01, -0.02, 0.03, -0.01, 0.02])
    got = variance(r, sample_weight=None, biased=False)
    assert np.isclose(got, np.var(r, ddof=1))
