# myapp.py

from random import randint
from datetime import datetime, timedelta

from bokeh.models import DateRangePicker, Toggle
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
import sqlite3

con = sqlite3.connect("electric-measures.db")
cur = con.cursor()


def build_date_range_picker():
    res = cur.execute(
        "SELECT datetime FROM production ORDER BY datetime DESC LIMIT 1"
    )
    max_range = res.fetchone()[0].split(' ')[0]

    res = cur.execute(
        "SELECT datetime FROM production ORDER BY datetime ASC LIMIT 1"
    )
    min_range = res.fetchone()[0].split(' ')[0]

    min_date = (
        datetime.strptime(max_range, '%Y-%m-%d') + timedelta(days=-7)
    ).strftime("%Y-%m-%d")

    return DateRangePicker(
        title="Select date range",
        value=(min_date, max_range),
        min_date=min_range,
        max_date=max_range,
        width=300,
    )


date_range_picker = build_date_range_picker()
toggle_grouped_by_day = Toggle(label="by day")


def build_datasource():

    startDateIncluded, endDateIncluded = date_range_picker.value
    grouped_by_day = toggle_grouped_by_day.active
    endDateExcluded = (
        datetime.strptime(endDateIncluded, '%Y-%m-%d') + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    if grouped_by_day:
        consumption_query = f"SELECT strftime('%Y-%m-%d 00:00:00', datetime) AS datetime, SUM(value) / 2 AS value FROM consumption WHERE datetime BETWEEN '{
            startDateIncluded}' AND '{endDateExcluded}' GROUP BY strftime('%Y-%m-%d', datetime) ORDER BY datetime"
    else:
        consumption_query = f"SELECT datetime, value FROM consumption WHERE datetime BETWEEN '{
            startDateIncluded}' AND '{endDateExcluded}'"
    res_consumption = cur.execute(consumption_query)
    consumption_data = res_consumption.fetchall()
    times = [
        datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for (t, _) in consumption_data
    ]
    consumption = [value for (_, value) in consumption_data]

    if grouped_by_day:
        production_query = f"SELECT strftime('%Y-%m-%d 00:00:00', datetime) AS datetime, SUM(value) / 2 AS value FROM production WHERE datetime BETWEEN '{
            startDateIncluded}' AND '{endDateExcluded}' GROUP BY strftime('%Y-%m-%d', datetime) ORDER BY datetime"
    else:
        production_query = f"SELECT datetime, value FROM production WHERE datetime BETWEEN '{
            startDateIncluded}' AND '{endDateExcluded}'"
    res_production = cur.execute(production_query)
    production_data = res_production.fetchall()
    production = [value for (_, value) in production_data]

    data = {
        'times': times,
        'production': production,
        'consumption': consumption,
    }
    return ColumnDataSource(data=data)


def update_plot(attr, old, new):
    src = build_datasource()
    source.data.update(src.data)


date_range_picker.on_change("value", update_plot)
toggle_grouped_by_day.on_change("active", update_plot)


min_x_range, max_x_range = date_range_picker.value
print(f'{min_x_range} to {max_x_range}')
p = figure(
    # x_range=(min_x_range, max_x_range),
    x_axis_type='datetime',
    title='Production and Consumption'
)

source = build_datasource()

# Plot stacked lines
p.step(
    x='times', y='production', source=source,
    color='blue', legend_label='Production',
    line_width=2
)
p.step(
    x='times', y='consumption', source=source,
    color='red', legend_label='Consumption',
    line_width=2
)

p.legend.location = "top_left"
p.legend.click_policy = "mute"


curdoc().add_root(row(p, column(date_range_picker, toggle_grouped_by_day)))
