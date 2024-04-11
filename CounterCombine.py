# vamos
import json
import sys
from datetime import datetime as dt
import datetime
import openpyxl
import pandas as pd
import xlsxwriter

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

    def save_stuff(self):
        self.workbook.close()


    # add -1s where values are missing (can happen for example, if there is no values for some counter in the last day,
    # therefore write_combined_values does not get called and no -1s are written at the end of this counter's column)
    def wrap_it_up(self, is_minutely):

        print("wrapping it up")

        for counter_name in self.counter_cols:
            row = self.counter_start_row[counter_name]
            counter_col = self.counter_cols[counter_name]

            while row < get_no_days_in_year(self.year)*get_values_for_day(is_minutely)+1:
                self.worksheet.write(row, counter_col, -1)
                row += 1
        print("done")


    def __init__(self, year, is_minutely):

        self.year = year
        self.is_minutely = is_minutely

        self.workbook = xlsxwriter.Workbook("./data/temp_worksheet.xlsx")
        self.worksheet = self.workbook.add_worksheet()

        self.worksheet = add_time_labels(self.worksheet, year, is_minutely)

        self.counter_cols = {}
        self.counter_start_row = {}

    def get_day(self, date):
        return date.split(".")[0]

    def get_month(self, date):
        return date.split(".")[1]

    def get_start_row(self, day, month):
        date_string = str(day)+"." + str(month)+"." + str(self.year)
        date_object = dt.strptime(date_string, '%d.%m.%Y')
        return (date_object.timetuple().tm_yday-1) * get_values_for_day(self.is_minutely) + 1

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


def add_counter_names(worksheet, counter_cols):

    start_col = 2
    for ctr_name in counter_cols:
        worksheet.write(0, start_col, ctr_name)
        start_col += 1

    return worksheet


def replace_null_values(counter_cols, year, is_minutely):

    print("replace null values start")

    data = pd.read_excel("./data/temp_worksheet.xlsx", header=0)
    coords = get_coords_of_ctrs()

    print("init worksheet")
    workbook = xlsxwriter.Workbook(get_combined_path_from_year(year, is_minutely))
    worksheet = workbook.add_worksheet() # todo you have two worksheet: one for writing to temp and one for writing to final file with the sam
    worksheet = add_time_labels(worksheet, year, is_minutely)
    worksheet = add_counter_names(worksheet, counter_cols)
    print("end of init")

    null_values = {}
    i = 0

    for counter_name in counter_cols:

        print("replacing null values for counter: " + counter_name + ", index: " + str(i))
        i += 1

        null_values[counter_name] = []

        for row in range(0, get_no_days_in_year(year)*get_values_for_day(is_minutely)):
            value = data.iloc[row, counter_cols[counter_name]]

            if row == 2352 and year == 2021 and not is_minutely:
                # todo: better implementation
                # todo: do it for other years also
                # break cause there is no more data after 8th of April
                break

            if value == -1:
                null_values[counter_name].append((row, True))
                worksheet.write(row+1, counter_cols[counter_name],
                                handle_null_value(data, row, counter_cols, counter_name,
                                    null_values, coords, is_minutely))
            elif value is not None:
                worksheet.write(row+1, counter_cols[counter_name], value)
                null_values[counter_name].append((row, False))
            else:
                break

    workbook.close()


def add_time_labels(worksheet, year, is_minutely):

    print("start init worksheet")
    start_date = dt(year=year, month=1, day=1)

    values_for_day = get_values_for_day(is_minutely)

    row_start = 1

    for i in range(get_no_days_in_year(year)):
        current_date = start_date + datetime.timedelta(days=i)
        worksheet.write(row_start, 0, current_date.strftime("%-d.%-m."))
        row_start += values_for_day

    row_start = 1
    time = dt(day=1, month=1, year=year, hour=0, minute=0)
    for i in range(get_no_days_in_year(year) * values_for_day):
        worksheet.write(row_start, 1, str(time.hour) + ":" + str(time.minute))
        row_start += 1
        time = increase_date_by(time, 1, is_minutely)

    print("init worksheet completed")

    return worksheet


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


def increase_date_by(date, amount, is_minutely):
    if is_minutely:
        return date + datetime.timedelta(minutes=amount*5)
    else:
        return date + datetime.timedelta(hours=amount)

def get_no_of_values_in_a_week(is_minutely):
    if is_minutely:
        return 24*12*7
    else:
        return 24*7


def get_values_from_prev_weeks(data, row, col, null_values_ctr, is_minutely):
    values_in_a_week = get_no_of_values_in_a_week(is_minutely)
    r = row - values_in_a_week
    limit = r - 5 * values_in_a_week
    if limit < 0:
        limit = 0
    while r > limit:
        value = data.iloc[r, col]
        if not null_values_ctr[r][1] and value != -1:
            return value
        r -= values_in_a_week
    return None


def find_coords_of_counter(coords, counter_name):
    for ctr_name, ctr_data in coords.items():
        if ctr_name[:-1] == counter_name:
            return ctr_data['latitude'], ctr_data['longitude']
    raise Exception("could not find coords of counter: " + counter_name)


def get_dist(ctr_data, lat, lon):
    lat_ctr = ctr_data['latitude']
    lon_ctr = ctr_data['longitude']
    return abs(lat_ctr-lat) + abs(lon_ctr-lon)


def get_lat_lan(ctr_data):
    lat = ctr_data['latitude']
    lon = ctr_data['longitude']
    return lat, lon


def get_value_from_counter(data, row, counter_name):
    return data.loc[:, counter_name].values.tolist()[row]


def get_value_from_closest_counter(data, coords, row, counter_cols, null_values, counter_name):

    if counter_name not in coords:
        return -1

    lat = coords[counter_name]['latitude']
    lon = coords[counter_name]['longitude']

    min_dist = sys.maxsize
    return_ctr_value = None

    values_for_day = data.iloc[row]

    for ctr_name, ctr_data in coords.items():
        dist = get_dist(ctr_data, lat, lon)

        value = values_for_day[counter_cols[ctr_name]]

        if ctr_name != counter_name and min_dist > dist and value != -1 \
                and ctr_name in null_values and not null_values[ctr_name][row][1]:
            min_dist = dist
            return_ctr_value = value

    if return_ctr_value is not None:
        return return_ctr_value
    else:
        return -1
        # raise Exception("could not find closest counter with non null value")


def is_next_value_null(data, r, c):
    if data.iloc[r+1, c] == -1:
        return True
    return False


def handle_null_value(data, row, counter_cols, counter_name, null_values, coords, is_minutely):

    if row > 0 and not null_values[counter_name][row-1][1] and not is_next_value_null(data, row,
                                                                                      counter_cols[counter_name]):
        return data.iloc[row-1, counter_cols[counter_name]]
    else:
        value_from_prev_weeks = get_values_from_prev_weeks(data, row, counter_cols[counter_name],
                                                           null_values[counter_name], is_minutely)
        if value_from_prev_weeks is not None:
            return value_from_prev_weeks
        else:
            return get_value_from_closest_counter(data, coords, row, counter_cols, null_values, counter_name)


def get_values_for_day(is_minutely):
    if is_minutely:
        return 288
    return 24


def get_no_days_in_year(year):
    if calendar.isleap(year):
        return 366
    return 365


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
        print("finished combining lanes for date: " + str(d) + ". " + str(m) + ", time: " + str(dt.now() - start_time))

    file_writer.wrap_it_up(is_minutely)

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

    # cc = {'0002-1': 2, '0002-2': 3, '0003-1': 4, '0003-2': 5, '0006-1': 6, '0006-2': 7, '0009-1': 8, '0009-2': 9, '0010-1': 10, '0010-2': 11, '0011-1': 12, '0013-1': 13, '0013-2': 14, '0015-1': 15, '0015-2': 16, '0016-1': 17, '0016-2': 18, '0017-1': 19, '0017-2': 20, '0018-1': 21, '0018-2': 22, '0019-1': 23, '0019-2': 24, '0020-1': 25, '0020-2': 26, '0025-1': 27, '0025-2': 28, '0026-1': 29, '0026-2': 30, '0031-1': 31, '0031-2': 32, '0034-1': 33, '0034-2': 34, '0035-1': 35, '0035-2': 36, '0037-1': 37, '0037-2': 38, '0038-1': 39, '0038-2': 40, '0040-1': 41, '0040-2': 42, '0041-1': 43, '0041-2': 44, '0042-1': 45, '0042-2': 46, '0044-1': 47, '0044-2': 48, '0046-1': 49, '0046-2': 50, '0048-1': 51, '0048-2': 52, '0049-1': 53, '0049-2': 54, '0051-1': 55, '0051-2': 56, '0052-1': 57, '0052-2': 58, '0054-1': 59, '0054-2': 60, '0055-1': 61, '0055-2': 62, '0056-1': 63, '0056-2': 64, '0057-1': 65, '0057-2': 66, '0060-1': 67, '0060-2': 68, '0061-1': 69, '0061-2': 70, '0062-1': 71, '0062-2': 72, '0064-1': 73, '0064-2': 74, '0067-1': 75, '0067-2': 76, '0068-1': 77, '0068-2': 78, '0069-1': 79, '0069-2': 80, '0070-1': 81, '0070-2': 82, '0071-1': 83, '0071-2': 84, '0072-1': 85, '0072-2': 86, '0073-1': 87, '0073-2': 88, '0074-1': 89, '0074-2': 90, '0077-1': 91, '0077-2': 92, '0079-1': 93, '0079-2': 94, '0081-1': 95, '0081-2': 96, '0082-1': 97, '0082-2': 98, '0083-1': 99, '0083-2': 100, '0084-1': 101, '0084-2': 102, '0085-1': 103, '0085-2': 104, '0086-1': 105, '0086-2': 106, '0087-1': 107, '0087-2': 108, '0088-1': 109, '0088-2': 110, '0090-1': 111, '0090-2': 112, '0092-1': 113, '0092-2': 114, '0095-1': 115, '0095-2': 116, '0096-1': 117, '0096-2': 118, '0097-1': 119, '0097-2': 120, '0099-1': 121, '0099-2': 122, '0100-1': 123, '0100-2': 124, '0101-1': 125, '0101-2': 126, '0102-1': 127, '0102-2': 128, '0103-1': 129, '0103-2': 130, '0104-1': 131, '0104-2': 132, '0105-1': 133, '0105-2': 134, '0106-1': 135, '0106-2': 136, '0107-1': 137, '0107-2': 138, '0108-1': 139, '0108-2': 140, '0109-1': 141, '0109-2': 142, '0111-1': 143, '0111-2': 144, '0112-1': 145, '0112-2': 146, '0114-1': 147, '0114-2': 148, '0115-1': 149, '0115-2': 150, '0116-1': 151, '0116-2': 152, '0117-1': 153, '0117-2': 154, '0118-1': 155, '0118-2': 156, '0119-1': 157, '0119-2': 158, '0120-1': 159, '0120-2': 160, '0121-1': 161, '0121-2': 162, '0122-1': 163, '0122-2': 164, '0123-1': 165, '0123-2': 166, '0124-1': 167, '0124-2': 168, '0125-1': 169, '0125-2': 170, '0126-1': 171, '0126-2': 172, '0127-1': 173, '0127-2': 174, '0128-1': 175, '0128-2': 176, '0129-1': 177, '0129-2': 178, '0131-1': 179, '0131-2': 180, '0132-1': 181, '0132-2': 182, '0133-1': 183, '0133-2': 184, '0134-1': 185, '0134-2': 186, '0136-1': 187, '0136-2': 188, '0137-1': 189, '0137-2': 190, '0138-1': 191, '0138-2': 192, '0139-1': 193, '0139-2': 194, '0140-1': 195, '0140-2': 196, '0141-1': 197, '0141-2': 198, '0142-1': 199, '0142-2': 200, '0143-1': 201, '0143-2': 202, '0146-1': 203, '0146-2': 204, '0148-1': 205, '0148-2': 206, '0149-1': 207, '0149-2': 208, '0150-1': 209, '0150-2': 210, '0153-1': 211, '0153-2': 212, '0154-1': 213, '0154-2': 214, '0155-1': 215, '0155-2': 216, '0156-1': 217, '0156-2': 218, '0160-1': 219, '0160-2': 220, '0161-1': 221, '0161-2': 222, '0163-1': 223, '0163-2': 224, '0164-1': 225, '0164-2': 226, '0165-1': 227, '0165-2': 228, '0166-1': 229, '0166-2': 230, '0167-1': 231, '0167-2': 232, '0168-1': 233, '0168-2': 234, '0172-1': 235, '0172-2': 236, '0174-2': 237, '0176-1': 238, '0176-2': 239, '0177-1': 240, '0177-2': 241, '0178-1': 242, '0178-2': 243, '0179-2': 244, '0180-1': 245, '0180-2': 246, '0186-1': 247, '0186-2': 248, '0188-1': 249, '0188-2': 250, '0189-1': 251, '0189-2': 252, '0190-1': 253, '0190-2': 254, '0192-1': 255, '0192-2': 256, '0193-1': 257, '0193-2': 258, '0194-1': 259, '0194-2': 260, '0196-1': 261, '0196-2': 262, '0198-1': 263, '0198-2': 264, '0199-1': 265, '0200-1': 266, '0200-2': 267, '0201-1': 268, '0201-2': 269, '0203-1': 270, '0203-2': 271, '0204-1': 272, '0204-2': 273, '0205-1': 274, '0205-2': 275, '0206-1': 276, '0206-2': 277, '0208-1': 278, '0208-2': 279, '0209-1': 280, '0209-2': 281, '0210-1': 282, '0210-2': 283, '0215-1': 284, '0215-2': 285, '0216-1': 286, '0216-2': 287, '0217-1': 288, '0217-2': 289, '0218-1': 290, '0218-2': 291, '0219-2': 292, '0220-1': 293, '0220-2': 294, '0221-1': 295, '0221-2': 296, '0222-1': 297, '0222-2': 298, '0227-1': 299, '0227-2': 300, '0228-1': 301, '0228-2': 302, '0229-1': 303, '0229-2': 304, '0230-1': 305, '0230-2': 306, '0231-1': 307, '0231-2': 308, '0232-1': 309, '0232-2': 310, '0233-1': 311, '0233-2': 312, '0234-1': 313, '0234-2': 314, '0235-1': 315, '0235-2': 316, '0237-1': 317, '0237-2': 318, '0241-1': 319, '0241-2': 320, '0242-1': 321, '0242-2': 322, '0244-1': 323, '0244-2': 324, '0245-1': 325, '0245-2': 326, '0246-1': 327, '0246-2': 328, '0247-1': 329, '0247-2': 330, '0248-1': 331, '0248-2': 332, '0249-1': 333, '0249-2': 334, '0250-1': 335, '0250-2': 336, '0252-1': 337, '0252-2': 338, '0255-1': 339, '0255-2': 340, '0256-1': 341, '0256-2': 342, '0258-1': 343, '0258-2': 344, '0259-1': 345, '0259-2': 346, '0260-1': 347, '0260-2': 348, '0262-1': 349, '0262-2': 350, '0264-1': 351, '0264-2': 352, '0265-1': 353, '0265-2': 354, '0267-1': 355, '0267-2': 356, '0268-1': 357, '0268-2': 358, '0270-1': 359, '0270-2': 360, '0271-1': 361, '0271-2': 362, '0273-1': 363, '0273-2': 364, '0275-1': 365, '0275-2': 366, '0277-1': 367, '0277-2': 368, '0278-1': 369, '0278-2': 370, '0279-1': 371, '0279-2': 372, '0280-1': 373, '0280-2': 374, '0281-1': 375, '0281-2': 376, '0283-1': 377, '0283-2': 378, '0284-1': 379, '0284-2': 380, '0285-1': 381, '0288-1': 382, '0288-2': 383, '0289-1': 384, '0289-2': 385, '0291-1': 386, '0291-2': 387, '0293-1': 388, '0293-2': 389, '0294-1': 390, '0294-2': 391, '0295-1': 392, '0295-2': 393, '0296-1': 394, '0296-2': 395, '0297-1': 396, '0297-2': 397, '0298-1': 398, '0298-2': 399, '0300-1': 400, '0300-2': 401, '0302-1': 402, '0302-2': 403, '0303-1': 404, '0303-2': 405, '0304-1': 406, '0304-2': 407, '0305-1': 408, '0305-2': 409, '0306-1': 410, '0306-2': 411, '0307-1': 412, '0307-2': 413, '0308-1': 414, '0308-2': 415, '0310-1': 416, '0310-2': 417, '0313-1': 418, '0313-2': 419, '0314-1': 420, '0314-2': 421, '0315-1': 422, '0315-2': 423, '0316-1': 424, '0316-2': 425, '0317-1': 426, '0317-2': 427, '0318-1': 428, '0318-2': 429, '0320-1': 430, '0320-2': 431, '0321-1': 432, '0321-2': 433, '0323-1': 434, '0323-2': 435, '0326-1': 436, '0326-2': 437, '0329-1': 438, '0329-2': 439, '0330-1': 440, '0330-2': 441, '0331-1': 442, '0331-2': 443, '0332-1': 444, '0332-2': 445, '0333-1': 446, '0333-2': 447, '0334-1': 448, '0334-2': 449, '0336-1': 450, '0336-2': 451, '0337-1': 452, '0337-2': 453, '0338-1': 454, '0338-2': 455, '0339-1': 456, '0339-2': 457, '0340-1': 458, '0340-2': 459, '0341-1': 460, '0341-2': 461, '0342-1': 462, '0342-2': 463, '0343-1': 464, '0343-2': 465, '0344-1': 466, '0344-2': 467, '0345-1': 468, '0345-2': 469, '0346-1': 470, '0346-2': 471, '0347-1': 472, '0347-2': 473, '0348-1': 474, '0348-2': 475, '0350-1': 476, '0350-2': 477, '0352-1': 478, '0352-2': 479, '0353-1': 480, '0353-2': 481, '0354-1': 482, '0354-2': 483, '0355-1': 484, '0355-2': 485, '0358-1': 486, '0358-2': 487, '0359-1': 488, '0359-2': 489, '0360-1': 490, '0360-2': 491, '0361-1': 492, '0361-2': 493, '0362-1': 494, '0362-2': 495, '0363-1': 496, '0363-2': 497, '0364-1': 498, '0364-2': 499, '0365-1': 500, '0365-2': 501, '0366-1': 502, '0366-2': 503, '0367-1': 504, '0367-2': 505, '0368-1': 506, '0368-2': 507, '0369-1': 508, '0369-2': 509, '0370-1': 510, '0370-2': 511, '0371-1': 512, '0371-2': 513, '0375-1': 514, '0375-2': 515, '0376-1': 516, '0376-2': 517, '0377-1': 518, '0377-2': 519, '0379-1': 520, '0379-2': 521, '0380-1': 522, '0380-2': 523, '0381-1': 524, '0381-2': 525, '0382-1': 526, '0382-2': 527, '0383-1': 528, '0383-2': 529, '0384-1': 530, '0384-2': 531, '0386-1': 532, '0386-2': 533, '0387-1': 534, '0387-2': 535, '0388-1': 536, '0388-2': 537, '0389-1': 538, '0389-2': 539, '0391-1': 540, '0391-2': 541, '0392-1': 542, '0392-2': 543, '0393-1': 544, '0393-2': 545, '0394-1': 546, '0394-2': 547, '0396-1': 548, '0396-2': 549, '0397-1': 550, '0397-2': 551, '0398-1': 552, '0398-2': 553, '0399-1': 554, '0399-2': 555, '0400-1': 556, '0400-2': 557, '0402-1': 558, '0402-2': 559, '0403-1': 560, '0403-2': 561, '0405-1': 562, '0405-2': 563, '0407-1': 564, '0407-2': 565, '0408-1': 566, '0408-2': 567, '0409-1': 568, '0409-2': 569, '0410-1': 570, '0410-2': 571, '0411-1': 572, '0411-2': 573, '0412-1': 574, '0412-2': 575, '0413-1': 576, '0413-2': 577, '0416-1': 578, '0416-2': 579, '0417-1': 580, '0417-2': 581, '0418-1': 582, '0418-2': 583, '0419-1': 584, '0419-2': 585, '0420-1': 586, '0420-2': 587, '0421-1': 588, '0421-2': 589, '0424-1': 590, '0424-2': 591, '0425-1': 592, '0425-2': 593, '0426-1': 594, '0426-2': 595, '0427-1': 596, '0427-2': 597, '0429-1': 598, '0429-2': 599, '0430-1': 600, '0430-2': 601, '0431-1': 602, '0431-2': 603, '0432-1': 604, '0432-2': 605, '0433-1': 606, '0433-2': 607, '0436-1': 608, '0436-2': 609, '0437-1': 610, '0437-2': 611, '0438-1': 612, '0438-2': 613, '0439-1': 614, '0439-2': 615, '0441-1': 616, '0441-2': 617, '0442-1': 618, '0442-2': 619, '0443-1': 620, '0443-2': 621, '0446-1': 622, '0446-2': 623, '0447-1': 624, '0447-2': 625, '0448-1': 626, '0448-2': 627, '0452-1': 628, '0452-2': 629, '0453-1': 630, '0453-2': 631, '0460-1': 632, '0460-2': 633, '0464-1': 634, '0464-2': 635, '0465-1': 636, '0465-2': 637, '0466-1': 638, '0466-2': 639, '0469-1': 640, '0469-2': 641, '0470-1': 642, '0470-2': 643, '0471-1': 644, '0471-2': 645, '0472-1': 646, '0472-2': 647, '0473-1': 648, '0473-2': 649, '0474-1': 650, '0474-2': 651, '0476-1': 652, '0476-2': 653, '0479-1': 654, '0479-2': 655, '0481-1': 656, '0481-2': 657, '0487-1': 658, '0487-2': 659, '0488-1': 660, '0488-2': 661, '0489-1': 662, '0489-2': 663, '0494-1': 664, '0494-2': 665, '0495-1': 666, '0495-2': 667, '0497-1': 668, '0497-2': 669, '0499-1': 670, '0499-2': 671, '0500-1': 672, '0500-2': 673, '0502-1': 674, '0502-2': 675, '0504-1': 676, '0504-2': 677, '0511-1': 678, '0511-2': 679, '0512-1': 680, '0512-2': 681, '0522-1': 682, '0522-2': 683, '0526-1': 684, '0526-2': 685, '0530-1': 686, '0530-2': 687, '0531-1': 688, '0531-2': 689, '0532-1': 690, '0532-2': 691, '0535-1': 692, '0535-2': 693, '0549-1': 694, '0549-2': 695, '0550-1': 696, '0550-2': 697, '0553-1': 698, '0553-2': 699, '0555-1': 700, '0555-2': 701, '0557-1': 702, '0557-2': 703, '0558-1': 704, '0558-2': 705, '0561-1': 706, '0561-2': 707, '0562-1': 708, '0562-2': 709, '0565-1': 710, '0565-2': 711, '0566-1': 712, '0566-2': 713, '0567-1': 714, '0567-2': 715, '0568-1': 716, '0568-2': 717, '0569-1': 718, '0569-2': 719, '0572-1': 720, '0572-2': 721, '0573-1': 722, '0573-2': 723, '0574-1': 724, '0574-2': 725, '0575-1': 726, '0575-2': 727, '0576-1': 728, '0576-2': 729, '0577-1': 730, '0577-2': 731, '0578-1': 732, '0578-2': 733, '0580-1': 734, '0580-2': 735, '0581-1': 736, '0581-2': 737, '0582-1': 738, '0582-2': 739, '0583-1': 740, '0583-2': 741, '0584-1': 742, '0584-2': 743, '0586-1': 744, '0586-2': 745, '0587-1': 746, '0587-2': 747, '0598-1': 748, '0598-2': 749, '0599-1': 750, '0599-2': 751, '0600-1': 752, '0600-2': 753, '0601-1': 754, '0601-2': 755, '0602-2': 756, '0603-1': 757, '0603-2': 758, '0604-1': 759, '0604-2': 760, '0605-1': 761, '0605-2': 762, '0606-1': 763, '0606-2': 764, '0607-1': 765, '0607-2': 766, '0608-1': 767, '0608-2': 768, '0609-1': 769, '0609-2': 770, '0610-1': 771, '0610-2': 772, '0611-1': 773, '0611-2': 774, '0612-1': 775, '0612-2': 776, '0613-1': 777, '0613-2': 778, '0614-1': 779, '0614-2': 780, '0615-1': 781, '0615-2': 782, '0616-1': 783, '0616-2': 784, '0617-1': 785, '0617-2': 786, '0619-1': 787, '0619-2': 788, '0620-1': 789, '0620-2': 790, '0621-1': 791, '0621-2': 792, '0622-1': 793, '0622-2': 794, '0623-1': 795, '0623-2': 796, '0624-1': 797, '0624-2': 798, '0625-1': 799, '0625-2': 800, '0627-1': 801, '0627-2': 802, '0630-1': 803, '0630-2': 804, '0631-1': 805, '0631-2': 806, '0632-1': 807, '0632-2': 808, '0634-1': 809, '0634-2': 810, '0635-1': 811, '0635-2': 812, '0636-1': 813, '0636-2': 814, '0637-1': 815, '0637-2': 816, '0638-1': 817, '0638-2': 818, '0639-1': 819, '0639-2': 820, '0641-1': 821, '0641-2': 822, '0643-1': 823, '0643-2': 824, '0644-1': 825, '0644-2': 826, '0645-1': 827, '0645-2': 828, '0646-1': 829, '0646-2': 830, '0647-1': 831, '0647-2': 832, '0648-1': 833, '0648-2': 834, '0650-1': 835, '0650-2': 836, '0652-1': 837, '0652-2': 838, '0653-1': 839, '0653-2': 840, '0654-1': 841, '0654-2': 842, '0655-1': 843, '0655-2': 844, '0657-1': 845, '0657-2': 846, '0658-1': 847, '0658-2': 848, '0659-1': 849, '0659-2': 850, '0660-1': 851, '0660-2': 852, '0661-1': 853, '0661-2': 854, '0662-1': 855, '0662-2': 856, '0663-1': 857, '0663-2': 858, '0664-1': 859, '0664-2': 860, '0665-1': 861, '0665-2': 862, '0666-1': 863, '0666-2': 864, '0667-1': 865, '0667-2': 866, '0668-1': 867, '0668-2': 868, '0669-1': 869, '0669-2': 870, '0670-1': 871, '0670-2': 872, '0671-1': 873, '0671-2': 874, '0673-1': 875, '0673-2': 876, '0674-1': 877, '0674-2': 878, '0675-1': 879, '0675-2': 880, '0676-1': 881, '0676-2': 882, '0678-1': 883, '0678-2': 884, '0681-1': 885, '0681-2': 886, '0683-1': 887, '0683-2': 888, '0684-1': 889, '0684-2': 890, '0686-1': 891, '0686-2': 892, '0687-1': 893, '0687-2': 894, '0688-1': 895, '0688-2': 896, '0689-1': 897, '0689-2': 898, '0690-1': 899, '0690-2': 900, '0691-1': 901, '0691-2': 902, '0692-1': 903, '0692-2': 904, '0693-1': 905, '0693-2': 906, '0694-1': 907, '0694-2': 908, '0695-1': 909, '0695-2': 910, '0696-1': 911, '0696-2': 912, '0697-1': 913, '0697-2': 914, '0699-1': 915, '0699-2': 916, '0700-1': 917, '0700-2': 918, '0702-1': 919, '0702-2': 920, '0706-1': 921, '0706-2': 922, '0707-1': 923, '0707-2': 924, '0708-1': 925, '0710-1': 926, '0710-2': 927, '0711-1': 928, '0711-2': 929, '0715-1': 930, '0715-2': 931, '0716-1': 932, '0716-2': 933, '0717-1': 934, '0717-2': 935, '0718-1': 936, '0718-2': 937, '0725-1': 938, '0725-2': 939, '0734-1': 940, '0734-2': 941, '0735-1': 942, '0735-2': 943, '0738-1': 944, '0738-2': 945, '0739-1': 946, '0739-2': 947, '0740-1': 948, '0740-2': 949, '0741-1': 950, '0741-2': 951, '0742-1': 952, '0742-2': 953, '0743-1': 954, '0743-2': 955, '0744-1': 956, '0744-2': 957, '0746-1': 958, '0746-2': 959, '0747-1': 960, '0747-2': 961, '0748-1': 962, '0748-2': 963, '0751-1': 964, '0751-2': 965, '0752-1': 966, '0752-2': 967, '0754-1': 968, '0754-2': 969, '0755-1': 970, '0755-2': 971, '0756-1': 972, '0756-2': 973, '0757-1': 974, '0757-2': 975, '0770-1': 976, '0770-2': 977, '0776-1': 978, '0776-2': 979, '0777-1': 980, '0777-2': 981, '0781-1': 982, '0781-2': 983, '0782-1': 984, '0782-2': 985, '0792-1': 986, '0792-2': 987, '0793-1': 988, '0793-2': 989, '0794-1': 990, '0794-2': 991, '0799-1': 992, '0799-2': 993, '0802-1': 994, '0802-2': 995, '0803-1': 996, '0803-2': 997, '0806-1': 998, '0806-2': 999, '0808-1': 1000, '0808-2': 1001, '0810-1': 1002, '0810-2': 1003, '0812-1': 1004, '0812-2': 1005, '0813-1': 1006, '0813-2': 1007, '0815-1': 1008, '0815-2': 1009, '0821-1': 1010, '0821-2': 1011, '0822-1': 1012, '0822-2': 1013, '0824-1': 1014, '0824-2': 1015, '0826-1': 1016, '0826-2': 1017, '0828-1': 1018, '0828-2': 1019, '0830-1': 1020, '0830-2': 1021, '0832-1': 1022, '0832-2': 1023, '0834-1': 1024, '0835-1': 1025, '0835-2': 1026, '0836-1': 1027, '0836-2': 1028, '0837-1': 1029, '0837-2': 1030, '0838-1': 1031, '0838-2': 1032, '0839-1': 1033, '0839-2': 1034, '0840-1': 1035, '0840-2': 1036, '0841-1': 1037, '0841-2': 1038, '0846-1': 1039, '0846-2': 1040, '0848-1': 1041, '0848-2': 1042, '0850-1': 1043, '0850-2': 1044, '0853-1': 1045, '0853-2': 1046, '0854-1': 1047, '0854-2': 1048, '0855-1': 1049, '0855-2': 1050, '0856-1': 1051, '0856-2': 1052, '0860-1': 1053, '0860-2': 1054, '0861-1': 1055, '0861-2': 1056, '0865-1': 1057, '0865-2': 1058, '0866-1': 1059, '0866-2': 1060, '0870-1': 1061, '0870-2': 1062, '0873-1': 1063, '0873-2': 1064, '0875-1': 1065, '0875-2': 1066, '0877-1': 1067, '0877-2': 1068, '0878-1': 1069, '0878-2': 1070, '0880-1': 1071, '0880-2': 1072, '0881-1': 1073, '0881-2': 1074, '0884-1': 1075, '0884-2': 1076, '0885-1': 1077, '0885-2': 1078, '0889-1': 1079, '0889-2': 1080, '0890-1': 1081, '0890-2': 1082, '0892-1': 1083, '0893-1': 1084, '0893-2': 1085, '0894-1': 1086, '0895-2': 1087, '0896-1': 1088, '0896-2': 1089, '0897-1': 1090, '0897-2': 1091, '0900-1': 1092, '0900-2': 1093, '0901-1': 1094, '0901-2': 1095, '0902-1': 1096, '0902-2': 1097, '0903-1': 1098, '0903-2': 1099, '0904-1': 1100, '0904-2': 1101, '0905-1': 1102, '0905-2': 1103, '0906-1': 1104, '0906-2': 1105, '0907-1': 1106, '0907-2': 1107, '0908-1': 1108, '0908-2': 1109, '0909-1': 1110, '0909-2': 1111, '0910-1': 1112, '0910-2': 1113, '0911-1': 1114, '0911-2': 1115, '0912-1': 1116, '0912-2': 1117, '0913-1': 1118, '0913-2': 1119, '0914-1': 1120, '0914-2': 1121, '0915-1': 1122, '0915-2': 1123, '0916-1': 1124, '0916-2': 1125, '0917-1': 1126, '0917-2': 1127, '0918-1': 1128, '0918-2': 1129, '0919-1': 1130, '0919-2': 1131, '0920-1': 1132, '0920-2': 1133, '0921-1': 1134, '0921-2': 1135, '0922-1': 1136, '0922-2': 1137, '0923-1': 1138, '0923-2': 1139, '0924-1': 1140, '0924-2': 1141, '0925-1': 1142, '0925-2': 1143, '0926-1': 1144, '0926-2': 1145, '0927-1': 1146, '0927-2': 1147, '0928-1': 1148, '0928-2': 1149, '0929-1': 1150, '0929-2': 1151, '0930-1': 1152, '0930-2': 1153, '0931-1': 1154, '0931-2': 1155, '0932-1': 1156, '0932-2': 1157, '0934-1': 1158, '0934-2': 1159, '0935-1': 1160, '0935-2': 1161, '0936-1': 1162, '0936-2': 1163, '0937-1': 1164, '0937-2': 1165, '0939-1': 1166, '0939-2': 1167, '1001-1': 1168, '1002-1': 1169, '1003-1': 1170, '1004-1': 1171, '1005-1': 1172, '1005-2': 1173, '1006-1': 1174, '1006-2': 1175, '1007-1': 1176, '1007-2': 1177, '1008-1': 1178, '1008-2': 1179, '1009-1': 1180, '1009-2': 1181, '1010-1': 1182, '1010-2': 1183, '1011-1': 1184, '1011-2': 1185, '1012-1': 1186, '1013-1': 1187, '1013-2': 1188, '1014-1': 1189, '1014-2': 1190, '1015-1': 1191, '1015-2': 1192, '1016-1': 1193, '1016-2': 1194, '1017-1': 1195, '1017-2': 1196, '1018-1': 1197, '1018-2': 1198, '1019-1': 1199, '1019-2': 1200, '1020-1': 1201, '1020-2': 1202, '1021-1': 1203, '1021-2': 1204, '1022-1': 1205, '1022-2': 1206, '1023-1': 1207, '1023-2': 1208, '1025-1': 1209, '1025-2': 1210, '1026-1': 1211, '1027-1': 1212, '1027-2': 1213, '1028-1': 1214, '1029-1': 1215, '1029-2': 1216, '1030-1': 1217, '1030-2': 1218, '1031-1': 1219, '1031-2': 1220, '1032-1': 1221, '1032-2': 1222, '1033-1': 1223, '1033-2': 1224, '1034-1': 1225, '1034-2': 1226, '1035-1': 1227, '1035-2': 1228, '1036-1': 1229, '1036-2': 1230, '1037-2': 1231, '1039-1': 1232, '1039-2': 1233, '1040-1': 1234, '1044-2': 1235, '1045-1': 1236, '1047-1': 1237, '1047-2': 1238, '1048-1': 1239, '1048-2': 1240, '1049-1': 1241, '1049-2': 1242, '1050-1': 1243, '1051-1': 1244, '1051-2': 1245, '1052-1': 1246, '1052-2': 1247, '1053-1': 1248, '1053-2': 1249, '1054-2': 1250, '1055-1': 1251, '0144-1': 1252, '0144-2': 1253, '0406-1': 1254, '0406-2': 1255, '0503-1': 1256, '0503-2': 1257, '0887-1': 1258, '0887-2': 1259, '0395-1': 1260, '0395-2': 1261}

    replace_null_values(file_writer.counter_cols, year, is_minutely)

#############################################################################################

test_file = False
combine_lanes_from_year(2019, is_minutely=False)
