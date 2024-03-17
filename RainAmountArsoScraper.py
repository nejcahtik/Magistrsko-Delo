from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import calendar
import datetime


url = "https://meteo.arso.gov.si/met/sl/app/webmet/#webmet==8Sdwx2bhR2cv0WZ0V2bvEGcw9ydlJWblR3LwVnaz9SYtVmYh9iclFGbt9SaulGdugXbsx3cs9mdl5WahxXYyNGapZXZ8tHZv1WYp5mOnMHbvZXZulWYnwCchJXYtVGdlJnOn0UQQdSf;"

chromeOptions = Options()
driver = webdriver.Chrome()
year = 2019


def is_leap_year(year):
    return calendar.isleap(year)


def get_no_of_days(year):
    if is_leap_year(year):
        return 366
    return 365

def init_stuff():
    driver.get(url)
    data_type = driver.find_elements(By.CLASS_NAME, "academa-archive-fieldset-content")[0]
    daily_data = data_type.find_elements(By.TAG_NAME, "table")[2]
    button = daily_data.find_element(By.CLASS_NAME, "academa-checkbox-button")
    button.click()
    station_type_container = driver.find_elements(By.CLASS_NAME, "academa-archive-fieldset-content")[1]

    station_types = station_type_container.find_elements(By.TAG_NAME, "table")

    for i in range(1, len(station_types)):
        station_types[i].find_element(By.CLASS_NAME, "academa-button").click()


def get_data_for_day():
    driver.find_elements(By.CLASS_NAME, "academa-tab-out")[0].click()
    table = driver.find_element(By.CLASS_NAME, "academa-archive-form-group")
    daily_measurements = table.find_elements(By.TAG_NAME, "td")[4]
    daily_measurements.find_element(By.CLASS_NAME, "academa-button").click()


start_date = datetime.date(year, 1, 1)
for day in range(get_no_of_days(year)):
    init_stuff()
    date_obj = start_date + datetime.timedelta(day)
    date_string = f"{date_obj.day:02d}.{date_obj.month:02d}"
    input_date = driver.find_element(By.ID, "_YCWBM47")
    input_date.send_keys(date_string)
    button = driver.find_elements(By.CLASS_NAME, "academa-button1")[7]
    button.click()

    get_data_for_day()




