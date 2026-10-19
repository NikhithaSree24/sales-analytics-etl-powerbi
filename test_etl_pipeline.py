
import pandas as pd
import pytest

from etl_pipeline import transform_data


def sample_data():
    """Create sample sales data for testing."""
    return pd.DataFrame({
        "Order_ID": [1, 2, 2, 3],
        "Order_Date": [
            "2023-01-10",
            "2023-02-15",
            "2023-02-15",
            "invalid-date"
        ],
        "Customer": ["A", "B", "B", "C"],
        "Region": ["East", "West", "West", "North"],
        "Product": ["Laptop", "Phone", "Phone", "Tablet"],
        "Sales": [1000, 800, 800, 500],
        "Cost": [700, 500, 500, 300]
    })


def test_transform_removes_duplicates_and_invalid_dates():
    """Check that duplicate rows and invalid dates are removed."""
    result = transform_data(sample_data())

    assert len(result) == 2
    assert result["Order_ID"].tolist() == [1, 2]


def test_profit_is_calculated_correctly():
    """Check that profit equals sales minus cost."""
    result = transform_data(sample_data())

    assert result["Profit"].tolist() == [300, 300]


def test_year_and_month_are_created():
    """Check that Year and Month columns are generated."""
    result = transform_data(sample_data())

    assert result["Year"].tolist() == [2023, 2023]
    assert result["Month"].tolist() == [1, 2]


def test_missing_required_column_raises_error():
    """Check that missing required columns are detected."""
    data = sample_data().drop(columns=["Sales"])

    with pytest.raises(ValueError, match="missing required columns"):
        transform_data(data)


def test_invalid_numeric_value_raises_error():
    """Check that invalid sales values are rejected."""
    data = sample_data()

    # Allow text in the Sales column for this test.
    data["Sales"] = data["Sales"].astype(object)
    data.loc[0, "Sales"] = "not-a-number"

    with pytest.raises(ValueError, match="invalid numeric values"):
        transform_data(data)
