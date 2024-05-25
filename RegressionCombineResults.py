import json
import numpy as np
import os

input_data_path = "./data/input_data.json"



# with open(input_data_path, 'r') as file:
#     input_data = json.load(file)
#
# no_of_nodes = input_data['no_of_nodes']
#
# counter_name = input_data['counter_name']

no_of_nodes = 100
counter_name = "0317-1"

prediction_errors = []
y_legit = []
y_predicted = []

directory = "./data/results_15_9_2019-0317-1/"

for i in range(no_of_nodes):
    try:
        pred_err_i = np.loadtxt(directory+"prediction_errs__no_add_f_"+counter_name+"-"+str(i)+".txt")
        y_legit_i = np.loadtxt(directory+"y_legit_values__no_add_f_"+counter_name+"-"+str(i)+".txt")
        y_predicted_i = np.loadtxt(directory+"y_pred_values__no_add_f_"+counter_name+"-"+str(i)+".txt")

        prediction_errors.append(pred_err_i)
        y_legit.append(y_legit_i)
        y_predicted.append(y_predicted_i)
    except Exception as e:
        print("error: " + str(i))

np.savetxt(directory+"prediction_errs_no_add_f_-"+counter_name+".txt", np.concatenate(prediction_errors, axis=0), fmt='%.2f')
np.savetxt(directory+"y_legit_values_no_add_f_-"+counter_name+".txt", np.concatenate(y_legit, axis=0), fmt='%.2f')
np.savetxt(directory+"y_pred_values_no_add_f_-"+counter_name+".txt", np.concatenate(y_predicted, axis=0), fmt='%.2f')

for i in range(no_of_nodes):
    try:
        os.remove(directory+"prediction_errs__no_add_f_"+counter_name+"-"+str(i)+".txt")
        os.remove(directory+"y_legit_values__no_add_f_"+counter_name+"-"+str(i)+".txt")
        os.remove(directory+"y_pred_values__no_add_f_"+counter_name+"-"+str(i)+".txt")
    except:
        print("error: " + str(i))

