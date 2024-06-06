# myapp.py

from random import randint
from datetime import datetime, timedelta

from bokeh.models import DateRangePicker, Toggle, RangeTool
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
import sqlite3

con = sqlite3.connect("electric-measures.db")
cur = con.cursor()

res = cur.execute(
    "SELECT datetime FROM production ORDER BY datetime DESC LIMIT 1"
)
max_range = res.fetchone()[0].split(' ')[0]
res = cur.execute(
    "SELECT datetime FROM production ORDER BY datetime ASC LIMIT 1"
)
min_range = res.fetchone()[0].split(' ')[0]
max_date = datetime.strptime(max_range, '%Y-%m-%d')
min_date = max_date + timedelta(days=-30)


def build_date_range_picker():
    return DateRangePicker(
        title="Select date range",
        value=(min_date.strftime("%Y-%m-%d"), max_range),
        min_date=min_range,
        max_date=max_range,
        width=300,
    )


date_range_picker = build_date_range_picker()
toggle_grouped_by_day = Toggle(label="by day", flow_mode="block")


def fetch_data(startDateIncluded, endDateIncluded):
    grouped_by_day = toggle_grouped_by_day.active
    endDateExcluded = (
        endDateIncluded + timedelta(days=1)
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
    consumption = [value / 1000 for (_, value) in consumption_data]

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
    production = [value / 1000 for (_, value) in production_data]

    gain = [(p - c) for c, p in zip(consumption, production)]

    return {
        'times': times,
        'production': production,
        'consumption': consumption,
        'gain': gain,
    }


def build_title(data):
    grouped_by_day = toggle_grouped_by_day.active

    if grouped_by_day:
        return f'total gain {sum(data["gain"])} kWh {sum(data["gain"]) * 0.25} € during the period'
    else:
        return f'total gail {sum(data["gain"]) / 2} kWh {sum(data["gain"]) / 2 * 0.25} € during the period'


def update_plot(startDateIncluded, endDateIncluded):
    data = fetch_data(startDateIncluded, endDateIncluded)
    src = ColumnDataSource(data=data)
    source.data.update(src.data)


p = figure(
    height=400, width=1000,
    toolbar_location=None,
    tools="xpan",
    x_axis_type="datetime",
    x_range=(min_date,  max_date)
)
p.yaxis.axis_label = 'kWh'

data = fetch_data(min_date, max_date)
source = ColumnDataSource(data=data)
title = build_title(data)

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

select = figure(title=title,
                height=200, width=1000,
                x_axis_type="datetime",
                tools="", toolbar_location=None)

range_tool = RangeTool(x_range=p.x_range)

select.line('times', 'gain', source=source)
select.ygrid.grid_line_color = None
select.add_tools(range_tool)


def update_range(attr, old, new):
    startDate, endDate = new
    update_plot(
        datetime.strptime(startDate, '%Y-%m-%d'),
        datetime.strptime(endDate, '%Y-%m-%d')
    )


date_range_picker.on_change("value", update_range)


def update_toggle(attr, old, new):
    startDate, endDate = date_range_picker.value
    update_plot(
        datetime.strptime(startDate, '%Y-%m-%d'),
        datetime.strptime(endDate, '%Y-%m-%d')
    )


toggle_grouped_by_day.on_change("active", update_toggle)


def update_range(attr, old, new):
    start = new["times"][0]
    end = new["times"][len(new["times"]) - 1]
    range_tool.x_range.start = start
    range_tool.x_range.end = end
    title = build_title(new)
    select.title.text = title


source.on_change('data', update_range)


curdoc().add_root(
    column(
        row(date_range_picker, toggle_grouped_by_day),
        p,
        select
    )
)
