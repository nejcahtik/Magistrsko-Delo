import datetime
import json
import math
import os
import random
import calendar
import matplotlib.pyplot as plt
import json
from haversine import haversine, Unit
from sklearn.linear_model import LassoCV
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge



from sklearn import preprocessing


import pandas as pd
from sklearn.linear_model import Lasso, LinearRegression
from datetime import datetime as dt

from sklearn.metrics import mean_squared_error
from sklearn.multioutput import MultiOutputRegressor

import sys
import WorkFreeDays
import numpy as np
import xlsxwriter

data_paths = {
    "2021": "./data/traffic_2021_combined.xlsx",
    "2020": "./data/traffic_2020_combined.xlsx",
    "2019": "./data/traffic_2019_combined.xlsx"
}

result_paths = {
    "2021": "./data/traffic_2021_regression_results.xlsx",
    "2020": "./data/traffic_2020_regression_results.xlsx",
    "2019": "./data/traffic_2019_regression_results.xlsx"
}


class AddFeatures:
    def __init__(self):
        self.add_features = 0
        self.add_feature_list = []

class FileWriter:

    def __init__(self, year):
        self.workbook = xlsxwriter.Workbook(result_paths[str(year)])
        self.worksheet = self.workbook.add_worksheet()

    def write_pred_values_to_file(self, data, pred_values, pred_ix):
        legit_values = get_row(data, pred_ix)

        if len(legit_values) != len(pred_values):
            raise Exception("something terrible has happened that shouldnt have")

        if self.worksheet.dim_rowmax is None:
            row = 0
        else:
            row = self.worksheet.dim_rowmax + 2

        for i in range(len(legit_values)):
            self.worksheet.write(row, i, legit_values[i])
            self.worksheet.write(row + 1, i, pred_values[i])

    def wrap_it_up(self):
        self.workbook.close()


def is_leap_year(year):
    return calendar.isleap(year)


def get_no_of_days(year):
    if is_leap_year(year):
        return 366
    return 365

def get_all_counter_names(data):
    return data.columns.tolist()[2:]


def get_random_counter_names(percentage):
    all_counters = data.columns.tolist()[2:]
    new_list_size = len(all_counters) // percentage

    return random.sample(all_counters, new_list_size)


def get_values_for_day(is_minutely):
    if is_minutely:
        return 288
    return 24


def get_date(minute, hour, day, month, year):
    return dt(year, month, day, hour, minute)


def get_counter_from(data, counter_name, row_start_ix, length):
    return data.loc[row_start_ix:row_start_ix + length - 1, counter_name].values


def get_work_day_value(pred_date):
    if WorkFreeDays.is_work_day(pred_date.day, pred_date.month, pred_date.year):
        return 0
    elif WorkFreeDays.is_saturday(pred_date.day, pred_date.month, pred_date.year):
        return 0.7
    else:
        # Sunday or holiday
        return 1


def get_all_columns_from(data, row_start_ix, length):
    return data.iloc[row_start_ix:row_start_ix + length, 2:].values.flatten()


def get_x_train_basic_test(data, x_train_start_ix, wind_len):
    return data.iloc[x_train_start_ix:x_train_start_ix + wind_len, 2:].values.flatten()


def get_row(data, ix):
    return data.iloc[ix, 2:].values


def get_feature_values_for_fixed_time_period(data, pred_date, x_train_start_ix, wind_len):
    x_train_basic = get_all_columns_from(data, x_train_start_ix, wind_len)
    return add_add_features(x_train_basic, pred_date)


def get_counter_value(data, row_ix, counter_name):
    return data.loc[:, counter_name].values.tolist()[row_ix]


def get_start_row(date, is_minutely):
    return (date.timetuple().tm_yday - 1) * get_values_for_day(is_minutely) + date.hour


def decrease_date_by(date, amount, is_minutely):
    if is_minutely:
        return date - datetime.timedelta(minutes=amount * 5)
    else:
        return date - datetime.timedelta(hours=amount)


def increase_date_by(date, amount, is_minutely):
    if is_minutely:
        return date + datetime.timedelta(minutes=amount * 5)
    else:
        return date + datetime.timedelta(hours=amount)


def get_feature_values(data, is_minutely, pred_date, wind_len, train_len):
    pred_date_ix = get_start_row(pred_date, is_minutely)
    x_train_start_ix = pred_date_ix - train_len - wind_len
    train_date = decrease_date_by(pred_date, train_len, is_minutely)

    x_train = []

    tp_ix = 0

    while x_train_start_ix < pred_date_ix - wind_len:
        x_train.append(
            get_feature_values_for_fixed_time_period(data, train_date, x_train_start_ix, wind_len).astype(float))

        x_train_start_ix += 1

        train_date = increase_date_by(train_date, 1, is_minutely)
        tp_ix += 1

    return x_train


def get_data_path(year, is_minutely):
    if not is_minutely:
        return data_paths[str(year)]


def cosine(value_degrees):
    return math.cos(math.radians(value_degrees))


def sine(value_degrees):
    return math.sin(math.radians(value_degrees))


def get_lat_lan(ctr_data):
    lat = ctr_data['latitude']
    lon = ctr_data['longitude']
    return lat, lon


def get_coords_of_ctrs():
    coords_file = json.load(open('./data/counters.json', 'r'))

    coords = {}

    for ctr_name, ctr_data in coords_file.items():
        lat, lon = get_lat_lan(ctr_data)

        # overrides counters on the same lane, doesn't matter since counters on the same lane
        # (btw this also holds for counters in the other direction) have the same coordinates
        coords[ctr_name[:-1]] = {'latitude': 0,
                                 'longitude': 0}
        coords[ctr_name[:-1]]['latitude'] = lat
        coords[ctr_name[:-1]]['longitude'] = lon

    return coords


def get_station_coords(name):
    lon_lat_vis = name.split(" ")[-3:]

    lon_sth = lon_lat_vis[0]
    lat_sth = lon_lat_vis[1]

    lon = lon_sth.split("=")[1]
    lat = lat_sth.split("=")[1]

    return float(lat), float(lon)


def get_consecutive_day_of_year(date):
    start_of_year = dt(date.year, 1, 1)
    consecutive_day = (date - start_of_year).days + 1
    return consecutive_day


def get_dist(station_lat, station_lon, cnt_lat, cnt_lon):
    station_coords = (station_lat, station_lon)
    cnt_coords = (cnt_lat, cnt_lon)

    return haversine(station_coords, cnt_coords, unit=Unit.KILOMETERS)


def get_closest_station_rain_snow_data(cnt_name):

    if cnt_name not in counter_coordinates:
        z = [0 for _ in range(get_no_of_days(year))]
        return z, z

    cnt_lat = counter_coordinates[cnt_name]['latitude']
    cnt_lon = counter_coordinates[cnt_name]['longitude']

    dist = sys.maxsize

    closest_station_name = ""

    i = 0

    for idx, station_name in enumerate(rain_data.columns):

        if idx % 2 == 1:
            station_lat, station_lon = get_station_coords(station_name)

            curr_dist = get_dist(station_lat, station_lon, cnt_lat, cnt_lon)

            if curr_dist < dist:
                dist = curr_dist
                closest_station_name = station_name
                i = idx

    final_rain_data = rain_data[closest_station_name].values
    final_snow_data = rain_data.iloc[:, i + 1].values

    if not final_rain_data.dtype == float:
        final_rain_data = np.array([float(x) if x != '' and x != ' ' else 0 for x in final_rain_data])
    if not final_snow_data.dtype == int:
        final_snow_data = np.array([int(x) if x != '' and x != ' ' else 0 for x in final_snow_data])

    return final_rain_data, final_snow_data


def get_rain_amount(date, cnt_name):
    rain_amount = rain_amount_data[cnt_name][get_consecutive_day_of_year(date)]
    return rain_amount


def get_snow_amount(date, cnt_name):
    return snow_amount_data[cnt_name][get_consecutive_day_of_year(date)]


def add_add_features(sample, pred_date):
    # if additional features are added, be aware - analyze_coefficients() is also using
    # no of additional featuers
    rain_amount = get_rain_amount(decrease_date_by(pred_date, 1, is_minutely), random_counter)
    snow_amount = get_snow_amount(decrease_date_by(pred_date, 1, is_minutely), random_counter)
    add_features = [cosine((360 / 60) * pred_date.minute), sine((360 / 60) * pred_date.minute),
                    cosine((360 / 24) * pred_date.hour), sine((360 / 24) * pred_date.hour),
                    cosine((360 / 7) * pred_date.weekday()), sine((360 / 7) * pred_date.weekday()),
                    cosine((360 / 31) * pred_date.day), sine((360 / 31) * pred_date.day),
                    cosine((360 / 12) * pred_date.month), sine((360 / 12) * pred_date.month),
                    cosine((360 / 365) * pred_date.timetuple().tm_yday),
                    sine((360 / 365) * pred_date.timetuple().tm_yday), rain_amount, snow_amount]

    for cnt_name in data.columns[2:]:
        cnt_rain_amount = get_rain_amount(decrease_date_by(pred_date, 1, is_minutely), cnt_name)
        cnt_snow_amount = get_snow_amount(decrease_date_by(pred_date, 1, is_minutely), cnt_name)
        add_features.append(cnt_rain_amount)
        add_features.append(cnt_snow_amount)
    af.add_features = len(add_features)
    af.add_feature_list = ["cos_min", "sin_min", "cos_hour", "sin_hour", "cos_weekday", "sin_weekday", "cos_day", "sin_day", "cos_month", "sin_month", "cos_day_in_year", "sin_day_in_year", "rain", "snow"]
    return np.concatenate((sample, add_features))


def get_y_train(data, counter_name, prediction_ix, train_len, wind_pred):
    y_train_start = prediction_ix - train_len
    y_train = []
    while y_train_start < prediction_ix:
        y_train.append(data.loc[y_train_start:y_train_start + wind_pred - 1, counter_name].values.astype(float))
        y_train_start += 1

    return y_train



def is_float_array(arr):
    return arr.dtype == float


def check_sizes(x_train, y_train, hour, day, month, year):

    for i in range(0, len(x_train)):
        size = len(x_train[0])
        if size != len(x_train[i]):
            raise Exception("sizes not ok for x_train: " + str(i) + " || " + str(hour) + ", " + str(day) + ", " + str(
                month) + ", " + str(year))
        if not is_float_array(x_train[i]):
            raise Exception(
                "x_train not float: " + str(i) + ", " + str(hour) + ", " + str(day) + ", " + str(month) + ", " + str(
                    year))

    for i in range(0, len(y_train)):
        size = len(y_train[0])
        if size != len(y_train[i]):
            raise Exception(
                "sizes not ok for y_train" + str(hour) + ", " + str(day) + ", " + str(month) + ", " + str(year))
        if not is_float_array(y_train[i]):
            raise Exception(
                "y_train not float: " + str(i) + ", " + str(hour) + ", " + str(day) + ", " + str(month) + ", " + str(
                    year))

    if len(y_train) != len(x_train):
        raise Exception(
            "xtrain and ytrain not the same size: " + str(hour) + ", " + str(day) + ", " + str(month) + ", " + str(
                year))


def analyze_coefficients(model):
    # print("---------------------------")
    # print("coefficients: ")

    no_of = af.add_features
    # check if this is correct

    avgs_per_day = []
    avgs_per_counter = []

    for estimator in model.estimators_:
        coefs = estimator.coef_

        cnts = coefs[:-af.add_features]
        add_f = coefs[len(cnts):]

        cnts_split_into_days = [cnts[i:i+len(counter_names)] for i in range(0, len(cnts), len(counter_names))]

        cnts_split_into_days_t = np.array(cnts_split_into_days).T

        avgs_per_counter.append([sum(cnts_split_into_days_t[i]) for i in range(len(cnts_split_into_days_t))])
        avgs_per_day.append([sum(cnts_split_into_days[i]) for i in range(len(cnts_split_into_days))])
        x_values = range(len(avgs_per_day[0]))

        # if len(avgs_per_day) % 8 == 0:
        plt.plot(x_values, avgs_per_day[-1], label="average coef value for prediction: " + str(len(avgs_per_day)))
        plt.title("Counter: " + random_counter + " | " + counter_location + ", " + str(day) + ". " + str(month) + ". " + str(year))
        plt.grid(True)
        plt.show()

        normalized_i = len(avgs_per_day) / len(model.estimators_)

        plt.bar(af.add_feature_list, add_f[:len(af.add_feature_list)], label="coefs for additional features: " + str(len(avgs_per_day)), color=(normalized_i/2,normalized_i/2,normalized_i))
        plt.title("Counter: " + random_counter + " | " + counter_location + ", " + str(day) + ". " + str(month) + ". " + str(year))
        plt.grid(True)
        plt.show()


    if(len(avgs_per_counter[0]) != len(counter_names)):
        raise Exception("something went to shit")

    dists = []
    dists_corr_cnts = []

    avg_values = []
    avg_values_corr_cnts = []


    if random_counter in weights:
        weights_cnt = weights[random_counter]
    else:
        weights_cnt = {}

    for i in range(len(avgs_per_counter[0])):
        cnt_name = counter_names[i]
        dists.append(distances_to_chosen_counter[cnt_name])
        avg_values.append(avgs_per_counter[0][i])
        # if cnt_name not in weights_cnt:
        #     dists.append(distances_to_chosen_counter[cnt_name])
        #     avg_values.append(avgs_per_counter[0][i])
        # else:
        #     dists_corr_cnts.append(distances_to_chosen_counter[cnt_name])
        #     avg_values_corr_cnts.append(avgs_per_counter[0][i])

    # plt.scatter(avg_values, dists, color="red")
    # plt.scatter(avg_values_corr_cnts, dists_corr_cnts, color="blue")

    fig = plt.figure(figsize=(10, 8))
    grid = plt.GridSpec(4, 4, hspace=0.2, wspace=0.2)

    main_ax = fig.add_subplot(grid[1:4, 0:3])
    main_ax.scatter(avg_values, dists)

    for i in range(len(counter_names)):
        if dists[i] is not None:
            main_ax.text(avg_values[i], dists[i], counter_names[i])

    main_ax.grid(True)
    main_ax.set_xlabel('Average value')
    main_ax.set_ylabel('Distance from the counter')

    x_hist = fig.add_subplot(grid[0, 0:3], sharex=main_ax)
    x_hist.hist(avg_values, bins=200, color='gray')
    x_hist.set_ylabel('Count')
    x_hist.set_yticks([])

    y_hist = fig.add_subplot(grid[1:4, 3], sharey=main_ax)
    dists_wo_none = [d if d is not None else 0 for d in dists]
    y_hist.hist(dists_wo_none, bins=300, orientation='horizontal', color='gray')
    y_hist.set_xlabel('Count')
    y_hist.set_xticks([])

    plt.grid(True)
    plt.title("Counter: " + random_counter + " | " + counter_location + ", " + str(day) + ". " + str(month) + ". " + str(year))
    plt.show()

    # print("---------------------------")



def lasso_regression(data, counter_name, is_minutely, pred_minute, pred_hour, pred_day,
                     pred_month, year, wind_len, train_len, pred_len, wind_pred):
    pred_date = get_date(pred_minute, pred_hour, pred_day, pred_month, year)

    # print("initializing data ...")
    prediction_ix = get_start_row(pred_date, is_minutely)

    x_train = get_feature_values(data,
                                 is_minutely,
                                 pred_date,
                                 wind_len, train_len)
    # print("xtrain")
    x_test = get_feature_values_for_fixed_time_period(data, pred_date, prediction_ix - wind_len, wind_len) \
        .reshape(1, -1)
    # print("ytrain")
    y_train = get_y_train(data, counter_name, prediction_ix, train_len, wind_pred)

    # print("done")

    file_writer = FileWriter(year)

    differences = []
    y_legits = []
    y_preds = []

    for i in range(pred_len):
        check_sizes(x_train, y_train, pred_hour, pred_day, pred_month, year)

        model = MultiOutputRegressor(Lasso(), n_jobs=-1)
        start_time = dt.now()

        scaler = preprocessing.MinMaxScaler()
        x_train = scaler.fit_transform(x_train)
        x_test = scaler.transform(x_test)

        # print("fitting")

        model.fit(x_train, y_train)

        train_time = dt.now() - start_time

        y_pred = model.predict(x_test)
        y_pred = y_pred[0]

        analyze_coefficients(model)

        y_legit = get_counter_from(data, counter_name, prediction_ix, wind_pred)


        difs = y_pred - y_legit
        difs_rel = difs / y_legit

        print(sum(difs_rel))

        differences.append(difs)

        y_legits.append(y_legit)
        y_preds.append(y_pred)

        pred_date = increase_date_by(pred_date, 1, is_minutely)
        prediction_ix += 1
        x_train = get_feature_values(data,
                                     is_minutely,
                                     pred_date,
                                     wind_len, train_len)

        x_test = get_feature_values_for_fixed_time_period(data, pred_date, prediction_ix - wind_len, wind_len) \
            .reshape(1, -1)
        y_train = get_y_train(data, counter_name, prediction_ix, train_len, wind_pred)


        file = open("./results/results_" + counter_name + "_" + str(consecutive_node_number) + ".txt", "a")
        file.write(str(i) + "/" + str(pred_len) + ", " + str(dt.now() - start_time))
        file.close()

        # print("progress: " + str(i + 1) + "/" + str(pred_len) + ", time: " + str(dt.now() - start_time) +
        #       ", train_time: " + str(train_time))
        # print("----------------------------------------------------------------")

    np.savetxt("./" + directory_name + "/prediction_errs_" + counter_name + "-" + str(
        consecutive_node_number) + ".txt", np.array(differences), fmt='%.2f')
    np.savetxt("./" + directory_name + "/y_legit_values_" + counter_name + "-" + str(
        consecutive_node_number) + ".txt", np.array(y_legits), fmt='%.2f')
    np.savetxt("./" + directory_name + "/y_pred_values_" + counter_name + "-" + str(
        consecutive_node_number) + ".txt", np.array(y_preds), fmt='%.2f')

    file_writer.wrap_it_up()


def remove_columns_and_get_file_path(percentage, year, is_minutely):
    number_of_all_counters = 1120  # todo: check if this number is correct

    if percentage == 100 or percentage == 0:
        return get_data_path(year, is_minutely)

    file_path = get_data_path(year, is_minutely)[:-5] + "_downsized_" + str(percentage) + ".xlsx"

    if os.path.exists(file_path):
        return file_path

    # raise Exception("input data file does not exist")

    print("removing columns ...")

    data = pd.read_excel(get_data_path(year, is_minutely), header=0)

    list_size = round(((100 - percentage) / 100) * number_of_all_counters)

    indeces_to_drop = sorted(random.sample(range(2, number_of_all_counters), list_size))

    data.drop(data.columns[indeces_to_drop], axis=1, inplace=True)

    data.to_excel(file_path, index=False)

    print("done")

    return file_path


def get_start_date(cons_nn, is_minutely, pred_len, year, month, day, hour, minute):
    sd = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    if is_minutely:
        start_date = sd + datetime.timedelta(minutes=cons_nn * (pred_len * 5))
    else:
        start_date = sd + datetime.timedelta(hours=cons_nn * pred_len)

    return start_date


def create_dir():
    if not os.path.exists(directory_name):
        os.mkdir(directory_name)
    else:
        pass


def get_rain_snow(data):
    rain = {}
    snow = {}
    for cnt_name in data.columns[2:]:


        r, s = get_closest_station_rain_snow_data(cnt_name)
        rain[cnt_name] = r
        snow[cnt_name] = s

    return rain, snow


def get_distances_to_counter(chosen_counter):

    if chosen_counter in counter_coordinates:
        coords_of_chosen_counter = counter_coordinates[chosen_counter]
    else:
        return [0 for _ in range(len(counter_names))]

    dists = {}


    for cnt_name in counter_names:

        if cnt_name not in counter_coordinates:
            dists[cnt_name] = None
            continue

        cnt_coords = counter_coordinates[cnt_name]


        dists[cnt_name] = get_dist(cnt_coords['latitude'], cnt_coords['longitude'],
                                   coords_of_chosen_counter['latitude'], coords_of_chosen_counter['longitude'])

    return dists


def get_weights():
    with open('./data/utezi.json', 'r') as json_file:
        w_data = json.load(json_file)

    return w_data


def get_counter_location(counter_name):
    with open('./data/counters.json', 'r') as json_file:
        counter_data = json.load(json_file)

    return counter_data[counter_name+"1"]["title"]


#########################################################################################################

input_data_path = "./data/input_data.json"

consecutive_node_number = int(sys.argv[1])

with open(input_data_path, 'r') as file:
    input_data = json.load(file)

start_year = input_data['start_date']['year']
start_month = input_data['start_date']['month']
start_day = input_data['start_date']['day']
start_hour = input_data['start_date']['hour']
start_minute = input_data['start_date']['minute']

all_pred_len = input_data['pred_len']

wind_len = input_data['wind_len']
train_len = input_data['train_len']
is_minutely = input_data['is_minutely']
wind_pred = input_data['wind_pred']
no_of_nodes = input_data['no_of_nodes']
counter_percentage = input_data['counter_percentage']
random_counter = input_data['counter_name']

actual_start_date = get_start_date(consecutive_node_number, is_minutely, all_pred_len // no_of_nodes,
                                   start_year, start_month, start_day, start_hour, start_minute)
year = actual_start_date.year
month = actual_start_date.month
day = actual_start_date.day
hour = actual_start_date.hour
minute = actual_start_date.minute

print(year, month, day, hour)


af = AddFeatures()

if consecutive_node_number == no_of_nodes - 1:
    pred_len = (all_pred_len // no_of_nodes) + (all_pred_len % no_of_nodes)
else:
    pred_len = all_pred_len // no_of_nodes

# year = 2020
# month = 6
# day = 30
# hour = 0
# minute = 0
#
# wind_len = 24*7
# train_len = 24*7*6
# is_minutely = False
# wind_pred = 24*7
# pred_len = 24*7*4


if get_start_row(get_date(minute, hour, day, month, year), is_minutely) < train_len:
    raise Exception("train length is longer than available data - ie you want to train the model on the data"
                    " that is not available because it is too far in the past")

file_path = remove_columns_and_get_file_path(counter_percentage, year, is_minutely)
print("data read start")
data = pd.read_excel(file_path, header=0)
print("data read finish")

rain_data = pd.read_excel("./data/raiaaaaan_" + str(year) + ".xlsx", header=0)

counter_names = get_all_counter_names(data)

counter_coordinates = get_coords_of_ctrs()

rain_amount_data, snow_amount_data = get_rain_snow(data)
weights = get_weights()


for i in range(40):

    random_counter = random.choice(counter_names)

    counter_location = get_counter_location(random_counter)
    directory_name = "./results_" + str(start_day) + "_" + str(start_month) + "_" + str(
        start_year) + "-" + random_counter
    create_dir()

    distances_to_chosen_counter = get_distances_to_counter(random_counter)

    lasso_regression(data, random_counter, is_minutely, minute, hour, day, month, year, wind_len, train_len, pred_len,
                     wind_pred)
