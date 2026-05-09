# House electricity consumption and production

Simple server displaying a dataviz with some interaction.
It uses Bokeh as dataviz tool and server.

It runs with uv:

```sh
uv run dataviz
```

This starts:

```sh
bokeh serve --show src/electric_meter/dataviz.py --allow-websocket-origin=192.168.1.170:5006
```

You can access
http://localhost:5006/dataviz

You can add --dev for reloading when code changes

On the back end, it's also:

- SQLite 3 for storing data
- https://www.myelectricaldata.fr/ for retrieving data from "Linky"

Fetch the next day of data with:

```sh
uv run fetch-daily-data
```

The SQLite database is intentionally kept at the repository root as
`electric-measures.db` so it can be backed up in git.
