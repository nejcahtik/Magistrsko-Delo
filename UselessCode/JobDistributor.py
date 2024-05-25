import datetime
import json

def increase_date_by(date, amount, is_minutely):
    if is_minutely:
        return date + datetime.timedelta(minutes=amount*5)
    else:
        return date + datetime.timedelta(hours=amount)


with open('../data/input_data.json', 'r') as file:
    input_data = json.load(file)

pred_len = input_data['pred_len']
is_minutely = input_data['is_minutely']
no_of_nodes = input_data['no_of_nodes']

year = input_data['start_date']['year']
month = input_data['start_date']['month']
day = input_data['start_date']['day']
hour = input_data['start_date']['hour']
minute = input_data['start_date']['minute']

start_date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

for i in range(no_of_nodes):

    if i == no_of_nodes-1:
        pred_len_new = pred_len % no_of_nodes
    else:
        pred_len_new = pred_len // no_of_nodes

    input_data['start_date']['year'] = start_date.year
    input_data['start_date']['month'] = start_date.month
    input_data['start_date']['day'] = start_date.day
    input_data['start_date']['hour'] = start_date.hour
    input_data['start_date']['minute'] = start_date.minute

    input_data['pred_len'] = pred_len_new

    with open("./data/input_file_"+str(i), "w") as json_file:
        json.dump(input_data, json_file)

    start_date = increase_date_by(start_date, pred_len, is_minutely)

