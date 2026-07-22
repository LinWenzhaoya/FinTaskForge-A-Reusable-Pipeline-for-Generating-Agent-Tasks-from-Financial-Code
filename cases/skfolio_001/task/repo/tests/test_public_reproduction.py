"""
公开复现测试: 复现 MaximumDiversification 在全负历史收益下的异常。
修复前: 抛 ValueError(任务中描述的现象)。
修复后: 应正常求解, 返回和为 1 的有效权重。
"""
import numpy as np
from skfolio.optimization import MaximumDiversification


def _negative_return_dataset():
    """4 个资产, 300 天, 所有资产历史平均收益均为负, 波动率各不相同。"""
    rng = np.random.default_rng(42)
    means = np.array([-0.0010, -0.0008, -0.0012, -0.0006])
    vols = np.array([0.010, 0.020, 0.015, 0.025])
    return rng.normal(loc=means, scale=vols, size=(300, 4))


def test_maximum_diversification_with_all_negative_returns():
    X = _negative_return_dataset()
    assert np.all(X.mean(axis=0) < 0)  # 前提: 所有资产平均收益为负

    model = MaximumDiversification()
    model.fit(X)  # 修复前这里会抛 ValueError

    assert model.weights_ is not None
    assert np.isclose(np.sum(model.weights_), 1.0)
