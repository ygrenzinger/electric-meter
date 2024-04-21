# House electricity consumption and production

Simple server displaying a dataviz with some interaction.
It uses Bokeh as dataviz tool and server.

It runs with:
bokeh serve --show dataviz.py
You can access
http://localhost:5006/dataviz

You can add --dev for reloading when code changes

On the back end, it's also:

- SQLite 3 for storing data
- https://www.myelectricaldata.fr/ for retrieving data from "Linky"
