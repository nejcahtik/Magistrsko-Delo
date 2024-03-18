# vamos
from datetime import datetime as dt
import datetime
import openpyxl
import pandas as pd
import xlsxwriter
from openpyxl import Workbook

import calendar
import numpy as np

data_paths = {
    "2021": {"hourly": "./data/traffic_2021.tab",
             "minutely": "./data/traffic_2021_5min.tab"
             },
    "2020": {"hourly": "./data/traffic_2020.tab",
             "minutely": "./data/traffic_2020_5min.tab"
             },
    "2019": {"hourly": "./data/traffic_2019.tab",
             "minutely": "./data/traffic_2019_5min.tab"
             }
}

data_paths_combined = {
    "2021": {
        "hourly": "./data/traffic_2021_combined.xlsx",
        "minutely": "./data/traffic_2021_combined_minutely.xlsx"
    },
    "2020": {"hourly": "./data/traffic_2020_combined.xlsx",
             "minutely": "./data/traffic_2020_combined_minutely.xlsx"
             },
    "2019": {
        "hourly": "./data/traffic_2019_combined.xlsx",
        "minutely": "./data/traffic_2019_combined_minutely.xlsx"
    }
}


class FileWriter:

    def get_no_days_in_year(self, year):
        if calendar.isleap(year):
            return 366
        return 365

    def save_stuff(self):
        self.workbook.close()

    def get_values_for_day(self, is_minutely):
        if is_minutely:
            return 288
        return 24

    def init_worksheet(self, year, is_minutely):

        print("start init worksheet")
        start_date = dt(year=year, month=1, day=1)

        values_for_day = self.get_values_for_day(is_minutely)

        row_start = 1

        for i in range(self.get_no_days_in_year(year)):
            current_date = start_date + datetime.timedelta(days=i)
            self.worksheet.write(row_start, 0, current_date.strftime("%-d.%-m."))
            row_start += values_for_day

        row_start = 1
        hour = 0
        for i in range(self.get_no_days_in_year(year) * values_for_day):
            self.worksheet.write(row_start, 1, f"{hour:02d}:00")
            row_start += 1
            hour += 1
            if hour > 23:
                hour = 0
        print("init worksheet completed")

    # add -1s where values are missing (can happen for example, if there is no values for some counter in the last day,
    # therefore write_combined_values does not get called and no -1s are written at the end of this counter's column)
    def wrap_it_up(self):

        for counter_name in self.counter_cols:
            row = self.counter_start_row[counter_name]
            counter_col = self.counter_cols[counter_name]

            while row < self.get_no_days_in_year(self.year):
                self.worksheet.write(row, counter_col, -1)
                row += 1

    def __init__(self, year, is_minutely):

        self.year = year
        self.is_minutely = is_minutely

        self.workbook = xlsxwriter.Workbook(get_combined_path_from_year(year, is_minutely))
        self.worksheet = self.workbook.add_worksheet()

        self.init_worksheet(year, is_minutely)

        self.counter_cols = {}
        self.counter_start_row = {}

    def get_day(self, date):
        return date.split(".")[0]

    def get_month(self, date):
        return date.split(".")[1]

    def get_start_row(self, day, month):
        date_string = str(day)+"." + str(month)+"." + str(self.year)
        date_object = dt.strptime(date_string, '%d.%m.%Y')
        return (date_object.timetuple().tm_yday-1) * self.get_values_for_day(self.is_minutely) + 1

    def write_combined_values_to_file_hourly(self, values, counter_name, day, month):

        counter_name = counter_name[:-1]

        if counter_name not in self.counter_cols:
            self.counter_cols[counter_name] = self.worksheet.dim_colmax + 1
            self.worksheet.write(0, self.counter_cols[counter_name], counter_name)

        counter_col = self.counter_cols[counter_name]

        if counter_name not in self.counter_start_row:
            self.counter_start_row[counter_name] = 1

        start_row = self.get_start_row(day, month)
        row = self.counter_start_row[counter_name]
        while row < start_row:
            self.worksheet.write(row, counter_col, -1)
            row += 1
        self.counter_start_row[counter_name] = start_row

        # Write the values to the target columns
        for row, value in enumerate(values, start=start_row):
            self.worksheet.write(row, counter_col, value)
        self.counter_start_row[counter_name] = self.counter_start_row[counter_name] + len(values)


    # def write_combined_values_to_file_minutely(self, no_of_vehicles, counter_value, day, month, year):
    #
    #     try:
    #         time = dt.strptime("00:00:00", "%H:%M:%S")
    #         for row in range(0, len(no_of_vehicles)):
    #             self.file.write(get_row_string(no_of_vehicles, get_counter_value_no_lanes_from_value(counter_value),
    #                                            time.strftime("%H:%M:%S"), day, month, year, row))
    #             time += datetime.timedelta(minutes=5)
    #     except Exception as e:
    #         raise e

    def write_combined_values_to_file(self, no_of_vehicles, counter_value, day, month, year, is_minutely):
        if is_minutely:
            # todo
            pass
            # self.write_combined_values_to_file_minutely(no_of_vehicles, counter_value, day, month, year)
        else:
            self.write_combined_values_to_file_hourly(no_of_vehicles, counter_value, day, month)


def get_counter_value_no_lanes_from_value(counter_value):
    return counter_value[:-1]


def get_combined_path_from_year(year, is_minutely):
    if not test_file:
        if not is_minutely:
            return data_paths_combined[str(year)]["hourly"]
        else:
            # return data_paths_combined[str(year)]["minutely"]
            pass
    else:
        # return "./data/final_test.tab"
        pass


def get_row_string(no_of_vehicles, counter_value, time, day, month, year, row):
    return str(year) + "\t" + str(month) + "\t" \
        + str(day) + "\t" + counter_value + "\t" + time \
        + "\t" + str(no_of_vehicles[row]) + "\n"


def get_vehicles_from_row(data, row):
    v = data.iloc[row, 5]
    if pd.isna(v):
        return -1
    else:
        return data.iloc[row, 5]


def get_hour_from_row(data, row):
    try:
        return data.iloc[row, 4]
    except:
        return -1


def get_daily_vehicles_by_day_for_counter(data, counter_ix):
    # print("get_daily_vehicles_by_hour_for_counter -> ")

    vehicles = []
    counter_value = get_counter_value(data, counter_ix)
    cix = counter_ix

    next_counter_value = get_counter_value(data, counter_ix)

    hour = 0
    number_of_values = 0

    while counter_value == next_counter_value:
        if get_hour_from_row(data, cix) == hour:
            vehicles.append(get_vehicles_from_row(data, cix))
            cix += 1
            number_of_values += 1
        else:
            vehicles.append(-1)
        hour += 1

        try:
            next_counter_value = get_counter_value(data, cix)
        except:
            break

    while len(vehicles) < 24:
        vehicles.append(-1)

    return vehicles, number_of_values


# ignore seconds
def is_equal_by_hour_and_minute(time1, time2):
    return time1[:5] == time2[:5]


def time_dif_between_in_mins(t1, t2):
    time1 = dt.strptime(t1, "%H:%M:%S")
    time2 = dt.strptime(t2, "%H:%M:%S")

    return (time1 - time2).total_seconds() / 60


def get_daily_vehicles_by_hour_for_counter(data, counter_ix):
    # print("get_daily_vehicles_by_hour_for_counter -> ")
    vehicles = []
    counter_value = get_counter_value(data, counter_ix)
    cix = counter_ix

    next_counter_value = get_counter_value(data, counter_ix)

    time = dt.strptime("00:00:00", "%H:%M:%S")
    number_of_values = 0

    # print("get_hour_from_row: " + counter_value + ", " + get_hour_from_row(data, cix) + ", day: " +
    # str(get_day_from_row(data, cix)))

    previous_time = None

    while counter_value == next_counter_value:
        # if counter_value == "0873-12":
        # print("hour_from_row: " + str(get_hour_from_row(data, cix)) + ", time:  " + time.strftime("%H:%M:%S"))

        if previous_time is not None and time_dif_between_in_mins(get_hour_from_row(data, cix), previous_time) < 5:
            cix += 1
            number_of_values += 1
            next_counter_value = get_counter_value(data, cix)
            continue
        else:
            if is_equal_by_hour_and_minute(get_hour_from_row(data, cix), time.strftime("%H:%M:%S")):
                vehicles.append(get_vehicles_from_row(data, cix))
                previous_time = get_hour_from_row(data, cix)
                cix += 1
                number_of_values += 1
            else:
                vehicles.append(0)

        time += datetime.timedelta(minutes=5)

        try:
            next_counter_value = get_counter_value(data, cix)
            # print("cix: " + str(cix) + ", " + next_counter_value + ", " + get_hour_from_row(data, cix))
        except:
            break

    while len(vehicles) < 288:  # = 12*24: 12 5-min intervals in one hour * 24 hours
        vehicles.append(0)

    return vehicles, number_of_values


def get_counter_value(data, counter_ix):
    # print("get_counter_value -> ")
    return data.iloc[counter_ix, 3]


def get_counter_value_test(data, counter_ix):
    # print("get_counter_value -> ")
    return data.iloc[counter_ix]


# returns name + direction
def get_counter_name_from_value(counter_value):
    try:
        return counter_value[:6]
    except:
        return ""


def get_counter_lane_from_value(counter_value):
    try:
        return counter_value[6:7]
    except:
        return ""


def combine_vehicle_numbers(v1, v2):
    # print("combine_vehicle_numbers -> ")

    for i in range(0, len(v1)):
        if v1[i] == -1:
            v1[i] = v2[i]
        elif v2[i] == -1:
            pass
        else:
            v1[i] += v2[i]
    return v1


def get_daily_vehicles_for_counter(data, counter_ix, is_minutely):
    if is_minutely:
        # return get_daily_vehicles_by_hour_for_counter(data, counter_ix)
        # todo doesnt work yet
        pass
    else:
        return get_daily_vehicles_by_day_for_counter(data, counter_ix)


# combines the counters that are on the same location and direction but on
# different lanes
def combine_counter(data, first_counter_row_num, day, month, year, is_minutely, file_writer):
    # print("combine_counter -> ")
    vehicles, rows_to_skip = get_daily_vehicles_for_counter(data, first_counter_row_num, is_minutely)

    counter_value = get_counter_value(data, first_counter_row_num)
    counter_name = get_counter_name_from_value(counter_value)
    counter_lane = get_counter_lane_from_value(counter_value)

    counter_ix_for_next_counter = first_counter_row_num + rows_to_skip

    try:
        next_counter_value = get_counter_value(data, counter_ix_for_next_counter)
    except Exception as e:
        file_writer.write_combined_values_to_file(vehicles, counter_value, day, month, year, is_minutely)
        return counter_ix_for_next_counter

    # add vehicle numbers together until there is a counter that is not on the same location and direction
    while counter_name == get_counter_name_from_value(next_counter_value) \
            and counter_lane != get_counter_lane_from_value(next_counter_value):

        vehicles_next_counter, rows_to_skip = get_daily_vehicles_for_counter(data, counter_ix_for_next_counter,
                                                                             is_minutely)
        vehicles = combine_vehicle_numbers(vehicles, vehicles_next_counter)

        counter_ix_for_next_counter += rows_to_skip
        try:
            next_counter_value = get_counter_value(data, counter_ix_for_next_counter)
        except Exception as e:
            file_writer.write_combined_values_to_file(vehicles, counter_value, day, month, year, is_minutely)
            return counter_ix_for_next_counter

    file_writer.write_combined_values_to_file(vehicles, counter_value, day, month, year, is_minutely)

    # print("counter_ix_for_next_counter: " + counter_ix_for_next_counter)
    return counter_ix_for_next_counter


def get_day_from_row(data, index):
    try:
        return data.iloc[index, 2]
    except:
        # end of the file
        return -1


def get_month_from_row(data, index):
    try:
        return data.iloc[index, 1]
    except:
        # end of the file
        return -1


def iterate_and_combine_counters_for_one_day(data, day, month, year, counter_start_ix, is_minutely, file_writer):
    # print("iterate_and_combine_counters_for_one_day -> ")

    # loop through all the counters for this day
    previous_day = day
    counter_ix = counter_start_ix

    while day > 0 and day == previous_day:
        # jump to next counter that is on the different location OR direction
        counter_ix = combine_counter(data, counter_ix, day, month, year, is_minutely, file_writer)
        # print("counter_ix: " + str(counter_ix))
        previous_day = day
        day = get_day_from_row(data, counter_ix)

    month = get_month_from_row(data, counter_ix)
    # return -1 if we've reached the end of the year
    return counter_ix, day, month


# combines values of the counters that have the same location and direction,
# count vehicles for different lanes
def combine_lanes(data, is_minutely, year, file_writer):
    counter_start_ix = 0
    day = get_day_from_row(data, counter_start_ix)
    month = get_month_from_row(data, counter_start_ix)
    while day > -1:
        start_time = dt.now()
        d = day
        m = month
        counter_start_ix, day, month = \
            iterate_and_combine_counters_for_one_day(data, day, month, year, counter_start_ix, is_minutely, file_writer)
        print("finished for date: " + str(d) + ". " + str(m) + ", time: " + str(dt.now() - start_time))

    file_writer.wrap_it_up()

def get_data_path(year, is_minutely):
    if is_minutely:
        return data_paths[str(year)]["minutely"]
    else:
        return data_paths[str(year)]["hourly"]


def combine_lanes_from_year(year, is_minutely):
    file_writer = FileWriter(year, is_minutely)
    if not test_file:
        try:
            data = pd.read_csv(get_data_path(year, is_minutely), delimiter='\t')
        except Exception as e:
            raise e
    else:
        data = pd.read_csv("./data/random.tab", delimiter='\t', header=None)
    combine_lanes(data, is_minutely, year, file_writer)
    file_writer.save_stuff()


# #########################################################################################

test_file = False
combine_lanes_from_year(2021, is_minutely=False)
