"""
Entry point for running the Dash AG-Grid Writeback application locally as a module.
Deployed apps run gunicorn instead (see app.yml).
"""

from .app import app
from .initialize_app import initialize_tables_on_startup

if __name__ == "__main__":
    initialize_tables_on_startup()
    app.run()  # set DASH_DEBUG=true for dev tools
