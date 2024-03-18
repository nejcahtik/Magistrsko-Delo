import math

import pandas as pd
from sklearn.linear_model import Lasso
from datetime import datetime as dt
import WorkFreeDays
import numpy as np

data_paths = {
    "2021": "./data/traffic_2021_combined.xlsx",
    "2020": "./data/traffic_2020_combined.xlsx",
    "2019": "./data/traffic_2019_combined.xlsx"
}


def get_all_counter_names(data):
    return data.columns.tolist()[2:]


def get_values_for_day( is_minutely):
    if is_minutely:
        return 288
    return 24


def get_date(minute, hour, day, month, year):
    return dt(year, month, day, hour, minute)


def get_work_day_value(pred_date):
    if WorkFreeDays.is_work_day(pred_date.day, pred_date.month, pred_date.year):
        return 0
    elif WorkFreeDays.is_saturday(pred_date.day, pred_date.month, pred_date.year):
        return 0.7
    else:
        # Sunday or holiday
        return 1


def get_x_train_basic(data, x_train_start_ix, wind_len):
    return data.iloc[x_train_start_ix:x_train_start_ix+wind_len, 2:].values.flatten()

def get_x_train_basic_test(data, x_train_start_ix, wind_len):

    while x_train_start_ix < x_train_start_ix + wind_len:
        d = data.iloc[x_train_start_ix, 2:].values.astype(int)
        print(d.dtype)
        nan_indices = np.where(np.isnan(d))
        print("-------------------------")
        print(nan_indices)
        print("x_train_start_ix: " + str(x_train_start_ix))

        x_train_start_ix += 1

    return data.iloc[x_train_start_ix:x_train_start_ix + wind_len, 2:].values.flatten()


def get_row(data, ix):
    return data.iloc[ix, 2:].values.tolist()


def get_feature_values_for_fixed_time_period(data, pred_date, wind_len, x_train_start_ix):
    x_train_basic = get_x_train_basic(data, x_train_start_ix, wind_len)
    return np.concatenate((x_train_basic,
                                    [get_work_day_value(pred_date), pred_date.hour, pred_date.day,
                                     pred_date.month]))


def get_counter_value(data, row_ix, counter_name):
    return data.loc[:, counter_name].values.tolist()[row_ix]


def get_start_row(date, is_minutely):
    return (date.timetuple().tm_yday - 1) * get_values_for_day(is_minutely) + date.hour


def check_for_nan(x):
    for i in range(len(x)):
        if x is None or x == "nan" or x == "NaN" or x == "None":
            print("x is none: " + str(i) + ", " + str(i/len(all_counter_names)) + ", " + str(i % len(all_counter_names)))

def get_feature_values(data, counter_name, is_minutely, pred_date, wind_len, train_len):
    pred_date_ix = get_start_row(pred_date, is_minutely)
    y_train_start_ix = pred_date_ix - train_len
    x_train_start_ix = y_train_start_ix - wind_len

    x_train = []
    y_train = []

    tp_ix = 0

    while y_train_start_ix < pred_date_ix:

        x_train.append(get_feature_values_for_fixed_time_period(data, pred_date, wind_len, x_train_start_ix).tolist())
        y_train.append(get_counter_value(data, y_train_start_ix, counter_name))

        y_train_start_ix += 1
        x_train_start_ix += 1

        tp_ix += 1

    return x_train, y_train


# params:
#   pred_day, pred_month - first day in the year for which values will be predicted
#   wind_len - number of days before prediction day that will be taken into account when predicting
#         values from including pred_day on
#   train_len - how big the training set will be (ie how far into the past the training will start)
#   values before index(pred_day, pred_month) - train_len - data_len will not be taken into an account for regression
def prepare_data(data, counter_name, is_minutely, pred_date, wind_len, train_len):

    x_train, y_train = get_feature_values(data, counter_name, is_minutely, pred_date, wind_len, train_len)
    x_test = get_feature_values_for_fixed_time_period(data, pred_date, wind_len, get_start_row(pred_date, is_minutely)
                                                      - wind_len).reshape(1, -1).tolist()

    return x_train, y_train, x_test


def get_data_path(year, is_minutely):
    if not is_minutely:
        return data_paths[str(year)]


def lasso_regression(data, is_minutely, pred_minute, pred_hour, pred_day, pred_month, year, wind_len, train_len):

    pred_date = get_date(pred_minute, pred_hour, pred_day, pred_month, year)
    cix = 0
    for counter_name in all_counter_names:
        start_time = dt.now()
        print("initializing learning data ...")
        x_train, y_train, x_test = prepare_data(data,
                                                counter_name,
                                                is_minutely,
                                                pred_date,
                                                wind_len, train_len)
        lasso = Lasso(alpha=0.3)
        print("learning ...")
        lasso.fit(x_train, y_train)
        print("predicting ...")
        y_pred = lasso.predict(x_test)

        y_legit = get_counter_value(data, get_start_row(pred_date, is_minutely), counter_name)

        print(str(y_pred) + ", " + str(y_legit) + " || dif: " + str(y_pred - y_legit))
        print("time period: " + str(cix) + "/" + str(train_len) + ", time: " + str(dt.now() - start_time))
        print("----------------------------------------------------------------")

        cix += 1


#########################################################################################################

# Input data
year = 2021
month = 3
day = 25
hour = 16
minute = 0
wind_len = 120
train_len = 24*50
is_minutely = False


if get_start_row(get_date(minute, hour, day, month, year), is_minutely) < train_len:
    raise Exception("train length is longer than available data - ie you want to train the model on the data"
                    " that is not available because it is too far in the past")

file_path = get_data_path(year, is_minutely)
print("data read start")
data = pd.read_excel(file_path, header=0)
print("data read finish")
all_counter_names = get_all_counter_names(data)
print(len(all_counter_names))
a = all_counter_names
lasso_regression(data, is_minutely, minute, hour, day, month, year, wind_len, train_len)
