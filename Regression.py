import datetime
import math
import random

import pandas as pd
from sklearn.linear_model import Lasso
from datetime import datetime as dt
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
    return data.iloc[ix, 2:].values


def get_feature_values_for_fixed_time_period(data, pred_date, x_train_start_ix, wind_len):
    x_train_basic = get_x_train_basic(data, x_train_start_ix, wind_len)
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


# params:
#   pred_day, pred_month - first day in the year for which values will be predicted
#   wind_len - number of days before prediction day that will be taken into account when predicting
#         values from including pred_day on
#   train_len - how big the training set will be (ie how far into the past the training will start)
#   values before (index(pred_day, pred_month) - train_len - data_len) will not be taken into an account for regression
def prepare_data(data, is_minutely, pred_date, wind_len, train_len):

    x_train = get_feature_values(data, is_minutely, pred_date, wind_len, train_len)

    return x_train


def get_data_path(year, is_minutely):
    if not is_minutely:
        return data_paths[str(year)]


def cosine(value):

    return math.cos((value-12)*(math.pi/12))+1


def add_add_features(sample, pred_date):
    return np.concatenate((sample, [get_work_day_value(pred_date), cosine(pred_date.hour), pred_date.day,
                                     pred_date.month]))


def get_y_train(data, counter_name, prediction_ix, train_len):
    return data.loc[prediction_ix-train_len:prediction_ix-1, counter_name].values


def modify_x_train(x_train, pred_values, new_date):
    # remove first sample
    x_train = x_train[1:]

    new_sample = x_train[-1]
    sample_size = len(x_train[0])
    no_of_additional_features = sample_size % len(all_counter_names)

    # remove first day of the sample
    new_sample = new_sample[len(pred_values):]

    # remove additional features
    new_sample = new_sample[:-no_of_additional_features]

    # add new values
    new_sample = np.concatenate((new_sample, pred_values))

    # add additional features
    new_sample = add_add_features(new_sample, new_date)

    x_train.append(new_sample)
    return x_train


def modify_x_test(x_test, pred_values, pred_date):
    sample_size = len(x_test[0])
    no_of_additional_features = sample_size % len(all_counter_names)
    new_x_test = x_test[0][len(pred_values):]
    new_x_test = new_x_test[:-no_of_additional_features]
    new_x_test = np.concatenate((new_x_test, pred_values))
    new_x_test = add_add_features(new_x_test, pred_date)
    return new_x_test.reshape(1, -1)


def lasso_regression(data, is_minutely, pred_minute, pred_hour, pred_day,
                     pred_month, year, wind_len, train_len, pred_len):

    pred_date = get_date(pred_minute, pred_hour, pred_day, pred_month, year)

    print("initializing training data ...")
    prediction_ix = get_start_row(pred_date, is_minutely)

    x_train = get_feature_values(data,
                 is_minutely,
                 pred_date,
                 wind_len, train_len)
    x_test = get_feature_values_for_fixed_time_period(data, pred_date, prediction_ix - wind_len, wind_len).reshape(1,-1)

    file_writer = FileWriter(year)

    for i in range(pred_len):

        curr_predicted_values = []

        for counter_name in all_counter_names:

            start_time = dt.now()

            y_train = get_y_train(data, counter_name, prediction_ix, train_len) #todo
            x_train = get_feature_values(data, is_minutely, pred_date, wind_len, train_len)

            lasso = Lasso(alpha=0.2)
            lasso.fit(x_train, y_train)

            y_pred = lasso.predict(x_test)
            y_legit = get_counter_value(data, get_start_row(pred_date, is_minutely), counter_name)


            print(str(y_pred) + ", " + str(y_legit) + " || dif: " + str(y_pred - y_legit))
            print("counters done: " + str(len(curr_predicted_values)) + "/" + str(len(all_counter_names)) +
                  ", time: " + str(dt.now() - start_time))
            print("----------------------------------------------------------------")

        file_writer.write_pred_values_to_file(data, curr_predicted_values, prediction_ix)

        pred_date = increase_date_by(pred_date, 1, is_minutely)
        x_train = modify_x_train(x_train, pred_date)
        x_test = modify_x_test(x_test, curr_predicted_values, pred_date)
        prediction_ix += 1

    file_writer.wrap_it_up()


#########################################################################################################

# Input data
year = 2021
month = 3
day = 25
hour = 16
minute = 0
wind_len = 10
train_len = 20
is_minutely = False
pred_len = 10

counter_downsize = 10

if get_start_row(get_date(minute, hour, day, month, year), is_minutely) < train_len:
    raise Exception("train length is longer than available data - ie you want to train the model on the data"
                    " that is not available because it is too far in the past")

file_path = get_data_path(year, is_minutely)
print("data read start")
data = pd.read_excel(file_path, header=0)
print("data read finish")
all_counter_names = get_random_counter_names(counter_downsize)
lasso_regression(data, is_minutely, minute, hour, day, month, year, wind_len, train_len, pred_len)
