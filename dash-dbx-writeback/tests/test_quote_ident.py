from dash_dbx_writeback.database_operations import quote_ident


def test_quote_ident_escapes_embedded_quotes():
    assert quote_ident("Product Name") == '"Product Name"'
    # A malicious CSV header must stay a single identifier
    assert quote_ident('x" text); DROP TABLE t; --') == '"x"" text); DROP TABLE t; --"'
