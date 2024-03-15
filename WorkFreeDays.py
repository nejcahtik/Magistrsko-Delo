import datetime


# dates of holidays
# in the form (day, month)
holidays = {
    2019: [
        (1, 1),
        (2, 1),
        (8, 2),  # 8th of Feburary -> Presheren's Day
        (21, 4),
        (22, 4),
        (27, 4),
        (1, 5),
        (2, 5),
        (9, 6),
        (25, 6),
        (15, 8),
        (31, 10),
        (1, 11),
        (25, 12),
        (26, 12),
    ],
    2020: [
        (1, 1),
        (2, 1),
        (8, 2),
        (12, 4),
        (13, 4),
        (27, 4),
        (1, 5),
        (2, 5),
        (31, 5),
        (25, 6),
        (15, 8),
        (31, 10),
        (1, 11),
        (25, 12),
        (26, 12),
    ],
    2021: [
        (1, 1),
        (2, 1),
        (8, 2),
        (4, 4),
        (5, 4),
        (27, 4),
        (1, 5),
        (2, 5),
        (23, 5),
        (25, 6),
        (15, 8),
        (31, 10),
        (1, 11),
        (25, 12),
        (26, 12),
    ]
}


def is_holiday(day, month, year):
    for values in holidays[year]:
        if values[0] == day and values[1] == month:
            return True
    return False


def is_sunday(day, month, year):
    given_date = datetime.date(year, month, day)
    day_of_week = given_date.weekday()
    return day_of_week == 6


def is_saturday(day, month, year):
    given_date = datetime.date(year, month, day)
    day_of_week = given_date.weekday()
    return day_of_week == 5


def is_weekend(day, month, year):
    return is_sunday(day, month, year) or is_saturday(day, month, year)


def is_work_day(day, month, year):
    return not (is_weekend(day, month, year) or is_holiday(day, month, year))


# returns true if there were lockdown restrictions due to
# covid-19 in place on this day
def is_corona_day(day, month, year):
    # todo
    pass
