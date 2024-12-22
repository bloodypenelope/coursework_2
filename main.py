import os
import json
import time
import datetime
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec
from dotenv import load_dotenv

from sql.sql_connector import MonitorSQLConnector
from utils.interpolate import rbf_interpolate


def get_structure_info(data, structure):
    stations = []
    points = []
    info = data[structure]

    size = info["size"]
    station_info = info["stations"]

    for station in station_info:
        stations.append(station["number"])
        coordinates = station["coordinates"]
        points.extend(coordinates)

    points = np.array(points)

    return size, stations, points


def get_values(connection, stations, timestamp, depth):
    values = []
    interval = 24 * 3600

    for station in stations:
        values.extend(connection.get_average_temperature(
            station, timestamp, interval, depth))

    return values


def update_depths(connection, data, structure, cbox):

    info = data[structure]

    station_num = info["stations"][0]["number"]
    depths = connection.get_depths(station_num)
    depths = list(map(lambda x: x / 10, sorted(depths)))

    cbox['values'] = depths


def plot(connection, data, structure, date, depth, fig, ax, canvas):
    timestamp = int(time.mktime(
        datetime.datetime.strptime(date, "%d/%m/%Y").timetuple()))
    depth = int(float(depth) * 10)

    size, stations, points = get_structure_info(data, structure)
    values = get_values(connection, stations, timestamp, depth)

    size_x, size_y = size
    grid_x = np.linspace(0, size_x, 100)
    grid_y = np.linspace(0, size_y, 100)
    grid_z = rbf_interpolate(points, values, grid_x, grid_y)

    x_coord, y_coord = points[:, 0], points[:, 1]

    ax.clear()
    if len(fig.axes) > 1:
        fig.delaxes(fig.axes[1])
        gs = gridspec.GridSpec(1, 1)
        ax.set_position(gs[0].get_position(fig))
        ax.set_subplotspec(gs[0])

    cax = ax.imshow(grid_z, extent=[0, size_x, 0, size_y],
                    origin='lower', cmap="rainbow")
    ax.scatter(x_coord, y_coord, c=values,
               cmap="rainbow", edgecolors="black")
    fig.colorbar(cax, shrink=0.8, aspect=20, pad=0.02)\
        .set_label('Температура °C')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Распределение температуры')
    canvas.draw()


def main():
    with open("data.json", mode="r", encoding="utf-8") as file:
        data = json.load(file)
        structures = data["structures"]

    load_dotenv()
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    database = os.getenv('DATABASE')

    connection = MonitorSQLConnector((host, port, user, password, database))

    depths = []

    root = tk.Tk()
    root.configure(background="white")

    fig, ax = plt.subplots()

    frame = tk.Frame(root)
    frame.configure(background="white")

    frame1 = tk.Frame(frame)
    frame1.configure(background="white")
    tk.Label(frame1, text="Расчет средней температуры за день в грунте",
             padx=10, pady=16, font=('calibre', 24), background="white")\
        .grid(columnspan=3)

    date = tk.StringVar()
    structure = tk.StringVar()
    depth = tk.StringVar()

    tk.Label(frame1, text="Введите дату:", font=('calibre', 12),
             background="white", padx=-10).grid(row=1, column=0)
    tk.Entry(frame1, textvariable=date, font=(
        'calibre', 12), width=16, highlightthickness=1,
        highlightbackground="gray").grid(row=2, column=0)

    tk.Label(frame1, text="Выберите здание:", font=('calibre', 12),
             background="white", padx=-10).grid(row=1, column=1)
    ttk.Combobox(frame1, textvariable=structure, values=structures, font=(
        'calibre', 12), width=18).grid(row=2, column=1)

    tk.Label(frame1, text="Выберите глубину:", font=('calibre', 12),
             background="white", padx=-10).grid(row=1, column=2)
    cbox = ttk.Combobox(frame1, textvariable=depth, values=depths, font=(
        'calibre', 12), width=12)
    cbox.grid(row=2, column=2)

    structure.trace_add(
        'write', lambda *_: update_depths(connection, data,
                                          structure.get(), cbox))

    frame1.pack(side=tk.TOP, pady=(20, 0))

    tk.Button(frame, text="Построить график", font=(
        'calibre', 12), width=16,
        command=lambda: plot(connection, data,
                             structure.get(), date.get(), depth.get(),
                             fig, ax, canvas)).pack(pady=(20, 0))

    frame.pack(side=tk.TOP, padx=10, pady=0)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(pady=0, side=tk.TOP)

    root.mainloop()


if __name__ == "__main__":
    main()
