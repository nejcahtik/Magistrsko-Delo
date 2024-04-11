import datetime
import math
import os
import random

import pandas as pd
from sklearn.linear_model import Lasso, LinearRegression
from datetime import datetime as dt

from sklearn.metrics import mean_squared_error
from sklearn.multioutput import MultiOutputRegressor

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


def get_all_counter_names(data):
    return data.columns.tolist()[2:]


def get_random_counter_names(percentage):
    all_counters = data.columns.tolist()[2:]
    new_list_size = len(all_counters) // percentage

    return random.sample(all_counters, new_list_size)


def get_values_for_day( is_minutely):
    if is_minutely:
        return 288
    return 24


def get_date(minute, hour, day, month, year):
    return dt(year, month, day, hour, minute)


def get_counter_from(data, counter_name, row_start_ix, length):
    return data.loc[row_start_ix:row_start_ix+length-1, counter_name].values


def get_work_day_value(pred_date):
    if WorkFreeDays.is_work_day(pred_date.day, pred_date.month, pred_date.year):
        return 0
    elif WorkFreeDays.is_saturday(pred_date.day, pred_date.month, pred_date.year):
        return 0.7
    else:
        # Sunday or holiday
        return 1


def get_all_columns_from(data, row_start_ix, length):
    return data.iloc[row_start_ix:row_start_ix+length, 2:].values.flatten()  # todo: flatten necessary?


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
        return date - datetime.timedelta(minutes=amount*5)
    else:
        return date - datetime.timedelta(hours=amount)


def increase_date_by(date, amount, is_minutely):
    if is_minutely:
        return date + datetime.timedelta(minutes=amount*5)
    else:
        return date + datetime.timedelta(hours=amount)


def get_feature_values(data, is_minutely, pred_date, wind_len, train_len):
    pred_date_ix = get_start_row(pred_date, is_minutely)
    x_train_start_ix = pred_date_ix - train_len - wind_len
    train_date = decrease_date_by(pred_date, train_len, is_minutely)

    x_train = []

    tp_ix = 0

    while x_train_start_ix < pred_date_ix - wind_len:

        x_train.append(get_feature_values_for_fixed_time_period(data, train_date, x_train_start_ix, wind_len))

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


def add_add_features(sample, pred_date):
    return np.concatenate((sample, [cosine((360/24)*pred_date.hour), sine((360/24)*pred_date.hour),
                                    cosine((360/7)*pred_date.weekday()), sine((360/7)*pred_date.weekday()),
                                     cosine((360/31)*pred_date.day), sine((360/31)*pred_date.day),
                                    cosine((360/12)*pred_date.month), sine((360/12)*pred_date.month),
                                    cosine((360/365)*pred_date.timetuple().tm_yday), sine((360/365)*pred_date.timetuple().tm_yday),
                                     ]))


def get_y_train(data, counter_name, prediction_ix, train_len, wind_pred):
    # print("prediction_ix: "  + str(prediction_ix-train_len))
    y_train_start = prediction_ix - train_len
    y_train = []
    while y_train_start < prediction_ix:
        y_train.append(data.loc[y_train_start:y_train_start+wind_pred-1, counter_name].values)
        y_train_start += 1

    return y_train


def modify_x_train(data, x_train, prediction_ix, pred_date):
    # remove first sample
    x_train = x_train[1:]

    new_sample = x_train[-1]
    sample_size = len(new_sample)
    no_of_additional_features = sample_size % len(counter_names)

    # remove first time period of the sample
    new_sample = new_sample[len(counter_names):]

    # remove additional features
    if no_of_additional_features != 0:
        new_sample = new_sample[:-no_of_additional_features]

    values_for_new_day = get_row(data, prediction_ix-2)

    # add new values
    new_sample = np.concatenate((new_sample, values_for_new_day))

    # # add additional features
    new_sample = add_add_features(new_sample, decrease_date_by(pred_date, 1, is_minutely))

    x_train.append(new_sample)
    return x_train


def modify_x_test(data, x_test, prediction_ix, pred_date):
    sample_size = len(x_test[0])
    no_of_additional_features = sample_size % len(counter_names)
    new_x_test = x_test[0][len(counter_names):]
    new_x_test = new_x_test[:-no_of_additional_features]
    new_data = get_row(data, prediction_ix-1)
    new_x_test = np.concatenate((new_x_test, new_data))
    new_x_test = add_add_features(new_x_test, pred_date)
    return new_x_test.reshape(1, -1)


def lasso_regression(data, is_minutely, pred_minute, pred_hour, pred_day,
                     pred_month, year, wind_len, train_len, pred_len, wind_pred):

    pred_date = get_date(pred_minute, pred_hour, pred_day, pred_month, year)

    print("initializing data ...")
    prediction_ix = get_start_row(pred_date, is_minutely)

    # random column
    counter_name = data.columns[40]

    x_train = get_feature_values(data,
                 is_minutely,
                 pred_date,
                 wind_len, train_len)
    x_test = get_feature_values_for_fixed_time_period(data, pred_date, prediction_ix - wind_len, wind_len)\
        .reshape(1, -1)
    y_train = get_y_train(data, counter_name, prediction_ix, train_len, wind_pred)

    print("done")

    file_writer = FileWriter(year)

    differences = []
    y_legits = []
    y_preds = []

    for i in range(pred_len):

        # curr_predicted_values = []
        # for counter_name in counter_names:
        start_time = dt.now()

        model = MultiOutputRegressor(LinearRegression())
        model.fit(x_train, y_train)

        y_pred = model.predict(x_test)
        y_legit = get_counter_from(data, counter_name, prediction_ix, wind_pred)
        # print(str(y_pred) + ", " + str(y_legit) + " || dif: " + str(y_pred - y_legit))

        # print(y_pred)
        # print(y_legit)
        # mse = mean_squared_error(y_legit, y_pred[0])
        difs = y_pred[0] - y_legit
        differences.append(difs)
        y_legits.append(y_legit)
        y_preds.append(y_pred[0])

        # print("Mean Squared Error:", mse)
        print("----------------------------------------------------------------")

        # file_writer.write_pred_values_to_file(data, curr_predicted_values, prediction_ix)

        pred_date = increase_date_by(pred_date, 1, is_minutely)
        prediction_ix += 1

        x_train = modify_x_train(data, x_train, prediction_ix, pred_date)
        x_test = modify_x_test(data, x_test, prediction_ix, pred_date)
        y_train = get_y_train(data, counter_name, prediction_ix, train_len, wind_pred)

        print("progress: " + str(i+1) + "/" + str(pred_len) + ", time: " + str(dt.now() - start_time))

    print("-----------------------------------------")
    print(differences)
    print("-----------------------------------------")
    np.savetxt("./data/prediction_errs_"+counter_name+".txt", np.array(differences), fmt='%.2f')
    np.savetxt("./data/prediction_errs_y_legit"+counter_name+".txt", np.array(y_legits), fmt='%.2f')
    np.savetxt("./data/prediction_errs_y_pred"+counter_name+".txt", np.array(y_preds), fmt='%.2f')

    file_writer.wrap_it_up()


def remove_columns_and_get_file_path(percentage, year, is_minutely):

    number_of_all_indexes = 1260  # todo: check if this number is correct

    if percentage == 0:
        return get_data_path(year, is_minutely)

    file_path = get_data_path(year, is_minutely)[:-5] + "_downsized_" + str(percentage) + ".xlsx"

    if os.path.exists(file_path):
        return file_path

    print("removing columns ...")

    data = pd.read_excel(get_data_path(year, is_minutely), header=0)

    list_size = round(((100-percentage)/100)*number_of_all_indexes)

    indeces_to_drop = sorted(random.sample(range(2, 1260), list_size))

    data.drop(data.columns[indeces_to_drop], axis=1, inplace=True)

    data.to_excel(file_path, index=False)

    print("done")

    return file_path


#########################################################################################################

# Input data
# start date
year = 2020
month = 6
day = 30
hour = 0
minute = 0

wind_len = 24*3
train_len = 24*15
is_minutely = False
wind_pred = 24*2
pred_len = 24*6

counter_percentage = 5


if get_start_row(get_date(minute, hour, day, month, year), is_minutely) < train_len:
    raise Exception("train length is longer than available data - ie you want to train the model on the data"
                    " that is not available because it is too far in the past")

file_path = remove_columns_and_get_file_path(counter_percentage, year, is_minutely)
print("data read start")
data = pd.read_excel(file_path, header=0)
print("data read finish")
counter_names = get_all_counter_names(data)
lasso_regression(data, is_minutely, minute, hour, day, month, year, wind_len, train_len, pred_len, wind_pred)
