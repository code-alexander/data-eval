"""Preset Semantic Layer scorers: the ready-made `metric_layer_equivalence` cascade."""

from evaldata.dbt.combinators import MetricFirstDecisive
from evaldata.dbt.metric_layer_judge import MetricLayerJudge
from evaldata.dbt.metric_result_equivalence import MetricResultEquivalence
from evaldata.dbt.metric_spec_equivalence import MetricSpecEquivalence
from evaldata.llm import Llm


def metric_layer_equivalence(model: str | Llm) -> MetricFirstDecisive:
    """The metric-query equivalence check ordered from cheapest to most expensive.

    Args:
        model: A litellm grader-model identifier, or an `Llm` to use directly, for the judge.

    Returns:
        A `MetricFirstDecisive` cascade: `MetricSpecEquivalence` compares the resolved queries
        first and exits early when it can decide; when it cannot, `MetricResultEquivalence` runs
        both queries and decides by their rows; when that is also inconclusive, `MetricLayerJudge`
        grades the queries.
    """
    return MetricFirstDecisive([MetricSpecEquivalence(), MetricResultEquivalence(), MetricLayerJudge(model)])
