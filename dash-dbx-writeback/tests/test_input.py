from dash import html
import dash_mantine_components as dmc
from dash_dbx_writeback.components.input import get_null_description, render_input_grid, COLUMN_DEFS, EDITABLE_FIELDS


def test_get_sample_data(custom_data):
    """Test the sample data structure and content"""
    assert isinstance(custom_data, list)
    assert len(custom_data) == 3

    # Check first product (Coles Milk)
    milk = custom_data[0]
    assert milk["LAYOUT_ID"] == "LAY001"
    assert milk["PRODUCT_NAME"] == "Coles Brand Milk 2L"
    assert milk["CATEGORY_NAME"] == "Dairy"
    assert milk["BRAND"] == "Coles"


def test_get_null_description_no_issues(custom_data):
    """Test null description with complete data"""
    result = get_null_description(custom_data)
    assert isinstance(result, dmc.Stack)


def test_get_null_description_with_issues(custom_data):
    """Test null description with missing required fields"""
    # Create a mutable copy of the data
    test_data = [row.copy() for row in custom_data]
    
    # Remove some required fields
    test_data[0]["LOYALTY_GROUP"] = None
    test_data[0]["SEGMENT_1"] = None

    result = get_null_description(test_data)
    assert isinstance(result, dmc.Stack)
    result_str = str(result)
    assert "LOYALTY_GROUP" in result_str
    assert "SEGMENT_1" in result_str


def test_column_definitions():
    """Test column definitions structure and content"""
    columns = COLUMN_DEFS

    assert isinstance(columns, list)
    assert len(columns) > 0

    # Check some key columns
    layout_col = next(col for col in columns if col["field"] == "LAYOUT_ID")
    assert layout_col["headerName"] == "Layout ID"

    # Check that LOYALTY_GROUP column exists
    loyalty_col = next(col for col in columns if col["field"] == "LOYALTY_GROUP")
    assert loyalty_col["headerName"] == "Loyalty Group"


def test_editable_fields_alignment():
    """Test that editable fields are properly defined"""
    # Get column definitions
    columns = COLUMN_DEFS

    # Check that all editable fields from the module have column definitions
    for field in EDITABLE_FIELDS:
        # Find the column definition for this field
        cols_with_field = [col for col in columns if col["field"] == field]
        assert len(cols_with_field) > 0, f"Field {field} should have a column definition"

    # Check that EDITABLE_FIELDS is not empty
    assert len(EDITABLE_FIELDS) > 0, "Should have at least some editable fields defined"


def test_render_input_grid_default():
    """Test rendering input grid with default data"""
    grid = render_input_grid()
    assert isinstance(grid, html.Div)

    # Check that all required components are present
    assert "grid-data-store" in str(grid)
    assert "ag-grid-table" in str(grid)
    assert "null-description-box" in str(grid)
    assert "csv-button" in str(grid)
    assert "submit-button" in str(grid)


def test_render_input_grid_custom_data(custom_data):
    """Test rendering input grid with custom data"""
    grid = render_input_grid()

    assert isinstance(grid, html.Div)
    assert "grid-data-store" in str(grid)
    assert "ag-grid-table" in str(grid)
