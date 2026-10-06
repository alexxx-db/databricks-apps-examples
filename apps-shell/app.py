import dash_mantine_components as dmc
from dash import html, dcc, Dash, page_registry, page_container, get_asset_url
from dash_iconify import DashIconify
from collections import defaultdict


def get_icon(icon):
    return DashIconify(icon=icon, height=16)


app = Dash(
    __name__,
    external_stylesheets=dmc.styles.ALL,
    use_pages=True,
    pages_folder="components",
)
server = app.server  # WSGI entrypoint for gunicorn (see app.yaml)

pages_by_category = defaultdict(list)
root_pages = []
for page in page_registry.values():
    category = page.get("category")
    if category:
        pages_by_category[category].append(page)
    else:
        root_pages.append(page)

category_links = []
for category, pages in pages_by_category.items():
    category_icon = pages[0].get("icon", "lucide:folder")

    category_links.append(
        dmc.NavLink(
            label=category.capitalize(),
            leftSection=get_icon(icon=category_icon),
            childrenOffset=28,
            children=[
                dmc.NavLink(
                    label=page["name"],
                    href=page["relative_path"],
                    active="partial",
                )
                for page in pages
            ],
        )
    )

root_links = [
    dmc.NavLink(
        label=page["name"],
        leftSection=get_icon(icon=page.get("icon", "lucide:table")),
        href=page["relative_path"],
        active="partial",
    )
    for page in root_pages
]

layout = dmc.AppShell(
    [
        dmc.AppShellHeader(children=[]),
        dmc.AppShellNavbar(
            id="navbar",
            children=[
                html.Div(
                    dcc.Link(
                        children=[
                            html.Img(
                                src=get_asset_url("logo.svg"), style={"height": 30}
                            ),
                        ],
                        href="/",
                    ),
                    style={
                        "display": "flex",
                        "justify-content": "flex-start",
                        "width": "100%",
                        "margin-top": "1.5rem",
                        "margin-bottom": "1.5rem",
                        "margin-left": "12px",
                    },
                ),
                *root_links,
                *category_links,
            ],
            p="lg",
            style={"background-color": "#EEEDE9"},
        ),
        dmc.AppShellMain(
            id="main", children=page_container, style={"background-color": "#F9F7F4"}
        ),
    ],
    header={"collapsed": True},
    padding="lg",
    navbar={
        "width": 300,
        "breakpoint": "sm",
        "collapsed": {"mobile": True},
    },
    id="appshell",
)


app.layout = dmc.MantineProvider(
    theme={
        "fontFamily": "DM Sans",
        "colors": {
            "lava": [
                "#ffe9e6",
                "#ffd2cd",
                "#ffa49a",
                "#ff7264",
                "#ff4936",
                "#ff2e18",
                "#ff1e07",
                "#e40f00",
                "#cc0500",
                "#b20000",
            ]
        },
        "primaryColor": "lava",
    },
    children=layout,
)

if __name__ == "__main__":
    app.run()  # local only; set DASH_DEBUG=true for dev tools
