import os

import folium
import json


def get_coordinates():
    with open("./data/counters.json") as f:
        data = json.load(f)

    counter_coordinates = []

    for element_key, element_value in data.items():
        counter_coordinates.append([element_value["latitude"], element_value["longitude"]])

    return counter_coordinates


def draw_counters():

    slovenia_coords = [46.120192, 14.815350]

    map_slovenia = folium.Map(location=slovenia_coords, zoom_start=8)

    point_coords = get_coordinates()

    for coords in point_coords:
        folium.Marker(coords, tooltip=f"Coordinates: {coords}").add_to(map_slovenia)

    return map_slovenia


def get_path_coords(data):

    paths = []

    for element_key, element_value in data.items():
        path_for_one_counter = []
        for coords in element_value["path"]:
            path_for_one_counter.append([coords[1], coords[0]])
        paths.append(path_for_one_counter)

    return paths


def draw_paths_of_counter(ctr_name, map):
    with open("./data/poti.json") as f:
        data = json.load(f)

    paths = None

    for element_key, element_value in data.items():
        if element_key == ctr_name:
            paths = get_path_coords(element_value)

    if paths is not None:
        for path in paths:
            for coords in path:
                folium.Marker(coords, icon=folium.Icon(color='green'),
                              tooltip=f"Coordinates: {coords}").add_to(map)

    return map_slovenia


map_slovenia = draw_counters()
map_slovenia = draw_paths_of_counter("0855-1", map_slovenia)

map_slovenia.save("./counters.html")
