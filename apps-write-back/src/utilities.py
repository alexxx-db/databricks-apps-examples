import dash_mantine_components as dmc
from flask import request


def current_user() -> str:
    """Signed-in user's email, added by the Databricks Apps proxy. Absent when running locally."""
    return request.headers.get("X-Forwarded-Email", "local-dev")


def make_radiocard(label, value, description):
    return dmc.RadioCard(
        value=value,
        withBorder=True,
        p="md",
        mt="md",
        bg="white",
        children=[
            dmc.Group(
                [
                    dmc.RadioIndicator(),
                    dmc.Box(
                        [
                            dmc.Text(label, lh="1.3", fz="md", fw="bold"),
                            dmc.Text(description, size="sm", c="dimmed"),
                        ]
                    ),
                ],
                wrap="nowrap",
                align="flex-start",
            )
        ],
    )
