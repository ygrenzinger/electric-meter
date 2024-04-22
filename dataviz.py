# myapp.py

from random import randint
from datetime import datetime, timedelta

from bokeh.models import DateRangePicker, Toggle, RangeTool
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, curdoc
import sqlite3

con = sqlite3.connect("electric-measures.db")
cur = con.cursor()

res = cur.execute(
    "SELECT datetime FROM production ORDER BY datetime DESC LIMIT 1"
)
max_range = res.fetchone()[0].split(' ')[0]
max_date = datetime.strptime(max_range, '%Y-%m-%d')


def build_date_range_picker():
    res = cur.execute(
        "SELECT datetime FROM production ORDER BY datetime ASC LIMIT 1"
    )
    min_range = res.fetchone()[0].split(' ')[0]
    return DateRangePicker(
        title="Select date range",
        value=(min_range, max_range),
        min_date=min_range,
        max_date=max_range,
        width=300,
    )


date_range_picker = build_date_range_picker()
toggle_grouped_by_day = Toggle(label="by day", flow_mode="block")


def fetch_data():
    startDateIncluded, endDateIncluded = date_range_picker.value
    grouped_by_day = toggle_grouped_by_day.active
    endDateExcluded = (
        datetime.strptime(endDateIncluded, '%Y-%m-%d') + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    if grouped_by_day:
        consumption_query = f"""
            SELECT strftime('%Y-%m-%d 00:00:00', datetime) AS datetime, SUM(value) / 2 AS value
            FROM consumption
            WHERE datetime
            BETWEEN '{startDateIncluded}' AND '{endDateExcluded}'
            GROUP BY strftime('%Y-%m-%d', datetime)
            ORDER BY datetime
        """
    else:
        consumption_query = f"""
            SELECT datetime, value
            FROM consumption
            WHERE datetime BETWEEN '{startDateIncluded}' AND '{endDateExcluded}'
        """
    res_consumption = cur.execute(consumption_query)
    consumption_data = res_consumption.fetchall()
    times = [
        datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for (t, _) in consumption_data
    ]
    consumption = [value for (_, value) in consumption_data]

    if grouped_by_day:
        production_query = f"""
            SELECT strftime('%Y-%m-%d 00:00:00', datetime) AS datetime, SUM(value) / 2 AS value
            FROM production
            WHERE datetime
            BETWEEN '{startDateIncluded}' AND '{endDateExcluded}'
            GROUP BY strftime('%Y-%m-%d', datetime)
            ORDER BY datetime
        """
    else:
        production_query = f"""
            SELECT datetime, value
            FROM production
            WHERE datetime BETWEEN '{startDateIncluded}' AND '{endDateExcluded}'
        """
    res_production = cur.execute(production_query)
    production_data = res_production.fetchall()
    production = [value for (_, value) in production_data]

    gain = [(p - c) for c, p in zip(consumption, production)]

    return {
        'times': times,
        'production': production,
        'consumption': consumption,
        'gain': gain,
    }


def update_plot(attr, old, new):
    data = fetch_data()
    src = ColumnDataSource(data=data)
    source.data.update(src.data)


date_range_picker.on_change("value", update_plot)
toggle_grouped_by_day.on_change("active", update_plot)


p = figure(
    height=400, width=1000,
    toolbar_location=None,
    tools="xpan",
    x_axis_type="datetime",
    x_range=(max_date + timedelta(days=-7),  max_date)
)
p.yaxis.axis_label = 'Watts'

data = fetch_data()
source = ColumnDataSource(data=data)

# Plot stacked lines
p.line(
    x='times', y='production', source=source,
    color='blue', legend_label='Production',
)

p.line(
    x='times', y='consumption', source=source,
    color='red', legend_label='Consumption',
)

p.legend.location = "top_left"
p.legend.click_policy = "mute"

select = figure(title="Drag the middle and edges of the selection box to change the range above",
                height=200, width=1000,
                x_axis_type="datetime",
                tools="", toolbar_location=None)

range_tool = RangeTool(x_range=p.x_range)

select.line('times', 'gain', source=source)
select.ygrid.grid_line_color = None
select.add_tools(range_tool)


curdoc().add_root(
    column(
        row(date_range_picker, toggle_grouped_by_day),
        p,
        select
    )
)
