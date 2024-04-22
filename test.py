from datetime import datetime as dt
import math
import matplotlib.pyplot as plt
import numpy as np


def draw_graph():
    points = [(1, 16.68975404), (2, 130.1635603), (3, 104.616433), (4, 124.0240618),
            (5, 82.2882722), (6, 311.1311038), (7, 677.4720455), (8, 3653.228496),
            (9, 2153.572528), (10, 3583.473677)]

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    plt.scatter(x_values, y_values, color='red', label='Prediction Sequence Number')

    plt.plot(x_values, y_values, color='blue', linestyle='-')

    plt.xlabel('Prediction Sequence Number')
    plt.ylabel('Sum of Relative Errors')
    plt.title('Relative Errors - Lasso Regression')

    plt.grid(True)

    plt.show()

def draw_graph_of_errors():

    loaded_array1 = np.loadtxt(pred_errs_path)
    t_loaded_array1 = loaded_array1.T

    legit_y_data = np.loadtxt(legit_y_path)

    fig, ax = plt.subplots()

    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Error')

    for i in range(len(t_loaded_array1)):
        if i % 8 == 0:
            ax.plot(np.arange(len(t_loaded_array1[i])) + i, np.abs(t_loaded_array1[i]), label="Prediction Time " + str(i+1))

    # ax2 = ax.twinx()
    # ax2.plot(legit_y_data, 'r-', label="Actual Values")
    # ax2.set_ylabel('Actual Values')
    # ax2.legend(loc='upper right')
    # ax.set_ylim(0, 200)



    # plt.plot(t_loaded_array1[20])

    # plt.legend([f'Prediction Time {8*i+1}' for i in range(len(t_loaded_array1))])
    ax.legend(loc='upper left')
    plt.title("Prediction Errors")
    plt.grid(True)
    plt.show()

def draw_actual_values():
    legit_y_data = np.loadtxt(legit_y_path)

    plt.plot(legit_y_data)
    plt.title("Actual Values for Counter 0561-2")
    plt.grid(True)
    plt.show()


def draw_graph_of_actual_vs_predicted():

    y_pred_t = np.loadtxt(pred_y_path)
    y_pred = y_pred_t.T
    y_legit = np.loadtxt(legit_y_path)

    pred_len = 24*7

    for i in range(len(y_pred)):
        if i % 10 == 0:
            plt.scatter(y_pred[i], y_legit[i:pred_len+i], label="Prediction Time " + str(i+1))

    plt.xlabel('Predicted Values')
    plt.ylabel('Actual Values')
    plt.title('Actual vs Predicted Values')
    plt.legend()
    plt.grid(True)
    plt.show()


def draw_avg_values_of_preds():
    y_pred_t = np.loadtxt(pred_errs_path)
    y_pred = y_pred_t.T

    avg_values = []

    for i in range(len(y_pred)):
        avg = 0
        for j in range(len(y_pred[i])):
            avg += np.abs(y_pred[i][j])

        avg = avg/len(y_pred[i])
        avg_values.append(avg)

    plt.plot(avg_values)
    plt.xlabel('Prediction Reach')
    plt.ylabel('Error')
    plt.title("Average Errors")
    plt.grid(True)
    plt.show()

def draw_errors_vs_predicted_value():

    y_pred_errs_t = np.loadtxt(pred_errs_path)
    y_pred_errs = y_pred_errs_t.T

    y_pred_t = np.loadtxt(pred_y_path)
    y_pred = y_pred_t.T

    # for i in range(len(y_pred)):
    #     if i % 5 == 0:
    #         plt.scatter(y_pred[i], y_pred_errs[i], label="Prediction Time: " + str(i+1))

    plt.scatter(y_pred[0], y_pred_errs[0], label="Prediction Time: " + str(1))

    plt.legend()
    plt.xlabel("Predicted Values")
    plt.ylabel("Error")

    plt.grid(True)
    plt.show()

def draw_with_vs_without_add_features():
    y_pred_t = np.loadtxt(pred_errs_path)
    y_pred = y_pred_t.T

    y_pred_t_w = np.loadtxt("./data/prediction_errs_"+counter_name+".txt")
    y_pred_w = y_pred_t_w.T

    avg_values = []
    avg_values_w = []
    dif = []

    fig, ax = plt.subplots()

    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Error')

    for i in range(len(y_pred)):
        avg = 0
        avg_w = 0

        if len(y_pred[i]) != len(y_pred_w[i]):
            raise Exception("arrays should be of same length")

        for j in range(len(y_pred[i])):
            avg += np.abs(y_pred[i][j])
            avg_w += np.abs(y_pred_w[i][j])

        dif.append(avg-avg_w)
        avg_values.append(avg/len(y_pred[i]))
        avg_values_w.append(avg_w/len(y_pred[i]))

    # ax.plot(np.arange(120), dif, label="With additional features")
    # ax.plot(np.arange(120), avg_values_w, label="Without additional features")

    ax.plot(np.arange(120), dif, label="Differences")

    plt.xlabel('Prediction Reach')
    plt.ylabel('Error')
    plt.title("Average Errors")
    plt.grid(True)
    plt.show()


counter_name = "0055-1"
pred_errs_path = "./data/"+counter_name+"/prediction_errs_"+counter_name+".txt"
legit_y_path = "./data/"+counter_name+"/prediction_errs_y_legit"+counter_name+".txt"
pred_y_path = "./data/"+counter_name+"/prediction_errs_y_pred"+counter_name+".txt"

draw_avg_values_of_preds()
