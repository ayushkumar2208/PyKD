from pykd.optimizer import QueryOptimizer
from pykd.planner import PlanNode


def test_table_scan_without_filter():
    optimizer = QueryOptimizer()

    plan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    result = optimizer.optimize(plan)

    assert result.operation == "TableScan"


def test_filter_becomes_index_scan():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    plan = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "id",
                "=",
                10,
            ),
        },
    )

    result = optimizer.optimize(plan)

    assert result.operation == "IndexScan"
    assert result.properties["table"] == "users"
    assert result.properties["column"] == "id"
    assert result.properties["operator"] == "="
    assert result.properties["value"] == 10


def test_range_condition_uses_index():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    plan = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "age",
                ">",
                18,
            ),
        },
    )

    result = optimizer.optimize(plan)

    assert result.operation == "IndexScan"


def test_non_indexable_condition_stays_filter():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    plan = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "name",
                "LIKE",
                "A%",
            ),
        },
    )

    result = optimizer.optimize(plan)

    assert result.operation == "Filter"


def test_filters_are_merged():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    first = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "age",
                ">",
                18,
            ),
        },
    )

    second = PlanNode(
        "Filter",
        children=(first,),
        properties={
            "condition": (
                "city",
                "=",
                "Delhi",
            ),
        },
    )

    result = optimizer.optimize(second)

    assert result.operation == "Filter"

    assert result.properties[
        "condition"
    ] == (
        "AND",
        ("age", ">", 18),
        ("city", "=", "Delhi"),
    )


def test_optimizer_preserves_projection():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    filter_node = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "id",
                "=",
                5,
            ),
        },
    )

    projection = PlanNode(
        "Projection",
        children=(filter_node,),
        properties={
            "columns": (
                "name",
            ),
        },
    )

    result = optimizer.optimize(projection)

    assert result.operation == "Projection"
    assert (
        result.children[0].operation
        == "IndexScan"
    )


def test_optimizer_handles_nested_nodes():
    optimizer = QueryOptimizer()

    scan = PlanNode(
        "TableScan",
        properties={
            "table": "users",
        },
    )

    filter_node = PlanNode(
        "Filter",
        children=(scan,),
        properties={
            "condition": (
                "id",
                "=",
                1,
            ),
        },
    )

    projection = PlanNode(
        "Projection",
        children=(filter_node,),
        properties={
            "columns": (
                "name",
            ),
        },
    )

    result = optimizer.optimize(projection)

    assert result.children[0].operation == "IndexScan"