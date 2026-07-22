"""
公开复现测试: variance 传入非均匀 sample_weight 时的行为。

现象: 给定一组非均匀权重, variance(returns, sample_weight=w, biased=True)
的返回值与按加权方差参考定义独立计算出的结果不一致。修复前本测试失败。
"""
import numpy as np
from skfolio.measures import variance


def test_weighted_variance_matches_reference():
    r = np.array([0.01, -0.02, 0.03, -0.01, 0.02])
    w = np.array([0.4, 0.3, 0.2, 0.05, 0.05])
    w = w / w.sum()

    got = variance(r, sample_weight=w, biased=True)

    # 加权(有偏)方差的参考值, 独立于被测实现
    ref_center = np.sum(w * r)
    expected = np.sum(w * (r - ref_center) ** 2)

    assert np.isclose(got, expected), (
        f"weighted variance result mismatch: got={got}, expected={expected}"
    )
