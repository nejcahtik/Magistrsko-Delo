import csv

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso

paths_json_path = "../data/poti.json"

data_paths = {
    "2021": "./data/traffic_2021_combined.tab",
    "2020": "./data/traffic_2020_combined.tab",
    "2019": "./data/traffic_2019_combined.tab"
}


def get_counter_value(data, counter_ix):
    try:
        return data.iloc[counter_ix, 3]
    except:
        return ""


def get_day_from_row(data, index):
    try:
        return data.iloc[index, 2]
    except:
        # end of the file
        return -1


def get_hour_from_row(data, row):
    try:
        return data.iloc[row, 4]
    except:
        return -1


def get_vehicle_numbers_by_row(data, row):
    v = data.iloc[row, 5]
    if pd.isna(v):
        return 0.0
    else:
        return data.iloc[row, 5]


def get_data_path(year, is_minutely):
    if not is_minutely:
        return data_paths[str(year)]


def get_month_from_row(data, index):
    try:
        return data.iloc[index, 1]
    except:
        # end of the file
        return -1

def get_zeroes(n):
    s = []
    for i in range(0, n):
        s.append(0)
    return s


def fix_len_x(x, ctr_name, len_x):
    try:
        l = len(x[ctr_name])
        while len(x[ctr_name]) != len_x:
            x[ctr_name].append(get_zeroes(24))
    except KeyError as e:
        x[ctr_name] = []
        while len(x[ctr_name]) != len_x:
            x[ctr_name].append(get_zeroes(24))
    return x


def get_counter_values_for_day(data, start_ix, pcn, pd, pm, x, day_no):
    start_day = get_day_from_row(data, start_ix)
    curr_ctr = get_counter_value(data, start_ix)
    previous_ctr = curr_ctr
    ix = start_ix

    vehicles_one_ctr_for_one_day = []

    while get_day_from_row(data, ix) == start_day:

        if previous_ctr == curr_ctr:
            vehicles_one_ctr_for_one_day.append(get_vehicle_numbers_by_row(data, ix))
        else:
            if len(vehicles_one_ctr_for_one_day) != 24:
                raise Exception("not enough values for counter: "
                                + str(previous_ctr) + " for day: "
                                + str(get_day_from_row(data, ix)) + ". " + str(get_month_from_row(data, ix)) + ", length: " + str(len(vehicles_one_ctr_for_one_day)))

            x = fix_len_x(x, previous_ctr, day_no)
            x[previous_ctr].append(vehicles_one_ctr_for_one_day)

            # reset array for another counter
            vehicles_one_ctr_for_one_day = [get_vehicle_numbers_by_row(data, ix)]
        previous_ctr = get_counter_value(data, ix)
        ix += 1
        curr_ctr = get_counter_value(data, ix)

    if len(vehicles_one_ctr_for_one_day) != 24:
        raise Exception("not enough values for counter: " + str(ix) + ", "
                        + str(curr_ctr) + " for day: "
                        + str(get_day_from_row(data, ix)) + ". " + str(get_month_from_row(data, ix)))

    x = fix_len_x(x, previous_ctr, day_no)
    x[previous_ctr].append(vehicles_one_ctr_for_one_day)

    return ix, x, day_no+1


# pc -> prediction counter
def remove_prediction_ctr(x, pcn):
    y = x.pop(pcn)
    return x, y


def split_into_train_test(x, y):
    test_indeces = [5, 29, 40, 45, 50, 64, 78, 91, 110, 112, 140, 149, 63]
    x_test = []
    y_test = []

    for ix in test_indeces:
        x_test.append(x[ix])
        x = np.delete(x, ix, axis=0)

        y_test.append(y[ix])
        y = np.delete(y, ix, axis=0)

    return x, y, x_test, y_test


# because not all counters appear in every day, array of 0s are added which substitue missing values for
# the days counters were missing
def make_xs_same_size(x, no_days):
    for key, value in x.items():
        while len(value) != no_days:
            value.append(get_zeroes(24))
    return x


def flatten(x):
    flattened = x.reshape(x.shape[0], -1)
    return flattened


def write_x_train_to_file(x):
    with open('x_train.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(x)

def write_x_test_to_file(x):
    with open('x_test.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(x)

def write_y_train_to_file(y):
    with open('y_train.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(y)

def write_y_test_to_file(y):
    np.savetxt("y_test.csv", y, delimiter=',')


def read_x_train_from_file():
    # Reading the 2D array back from the CSV file
    read_data = []
    with open('x_train.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            read_data.append([int(x) for x in row])
    return read_data

def read_x_test_from_file():
    # Reading the 2D array back from the CSV file
    read_data = []
    with open('x_test.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            read_data.append([int(x) for x in row])
    return read_data

def read_y_train_from_file():
    # Reading the 2D array back from the CSV file
    read_data = []
    with open('y_train.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            read_data.append([int(x) for x in row])
    return read_data

def read_y_test_from_file():
    # Reading the 2D array back from the CSV file
    read_data = []
    with open('y_test.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            read_data.append([int(x) for x in row])
    return read_data


# pcn -> counter name that we will predict
# pd, pm -> day and month when the values of the counter pcn that we will predict are
def prepare_data(data, pcn, pd, pm, pred_day_ix):

    curr_day = get_day_from_row(data, 0)

    x = {}
    new_ix = 0
    day_no = 0

    # while curr_day > -1:
    while curr_day != -1:
        print("day_ix: " + str(day_no))
        new_ix, x, day_no = get_counter_values_for_day(data, new_ix, pcn, pd, pm, x, day_no)
        curr_day = get_day_from_row(data, new_ix)

    x = make_xs_same_size(x, day_no)
    x, y = remove_prediction_ctr(x, pcn)
    x = np.array([value for value in x.values()])
    y = np.array(y)
    x = flatten(x)
    y = y.flatten()
    x = x.T
    x_train, y_train, x_test, y_test = split_into_train_test(x, y)

    return x_train, y_train, x_test, y_test


def lasso_regression(year, is_minutely, pred_ctr_name, day, month, pred_day_ix):
    data = pd.read_csv(get_data_path(year, is_minutely), delimiter='\t', header=None)
    x_train, y_train, x_test, y_test = prepare_data(data, pred_ctr_name, day, month, pred_day_ix)
    lasso = Lasso(alpha=0.3)
    lasso.fit(x_train, y_train)
    y_pred = lasso.predict(x_test)

    return y_pred, y_test


prediction_day_ix = 47
y_pred, legit_y = lasso_regression(2021, False, "0855-1", 7, 24, prediction_day_ix)

print(y_pred)
print(legit_y)
