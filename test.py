from datetime import datetime as dt
import math
import matplotlib.pyplot as plt
import numpy as np


def cosine(value):

    return math.cos((value-12)*(math.pi/12))+1


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
    file_path1 = "./data/prediction_errs_0056-2.txt"
    file_path2 = "./data/prediction_errs_0561-2.txt"
    legit_y_path = "./data/prediction_errs_y_legit0561-2.txt"

    loaded_array1 = np.loadtxt(file_path2)
    t_loaded_array1 = loaded_array1.T

    legit_y_data = np.loadtxt(legit_y_path)

    fig, ax = plt.subplots()

    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Error')

    for i in range(len(t_loaded_array1)):
        if i % 8 == 0:
            ax.plot(np.arange(len(t_loaded_array1[i])) + i, t_loaded_array1[i], label="Prediction Time" + str(i+1))

    ax2 = ax.twinx()
    ax2.plot(legit_y_data, 'r-', label="Actual Values")
    ax2.set_ylabel('Actual Values')
    # ax.plot(legit_y_data)

    # plt.plot(t_loaded_array1[20])

    # plt.legend([f'Prediction Time {8*i+1}' for i in range(len(t_loaded_array1))])
    ax.legend(loc='upper left')
    ax.set_ylim(0, 400)
    ax2.legend(loc='upper right')
    plt.title("Prediction Errors")
    plt.show()

def draw_actual_values():
    legit_y_path = "./data/prediction_errs_y_legit0561-2.txt"
    legit_y_data = np.loadtxt(legit_y_path)

    plt.plot(legit_y_data)
    plt.title("Actual Values for Counter 0561-2")
    plt.grid(True)
    plt.show()


def draw_graph_of_actual_vs_legit():
    legit_path = "./data/prediction_errs_y_legit0561-2.txt"
    pred_path = "./data/prediction_errs_y_pred0561-2.txt"

    y_pred_t = np.loadtxt(pred_path)
    y_pred = y_pred_t.T
    y_legit = np.loadtxt(legit_path)

    pred_len = 24*5

    for i in range(len(y_pred)):
        if i % 10 == 0:
            plt.scatter( y_pred[i], y_legit[i:pred_len+i])

    plt.xlabel('Predicted Values')
    plt.ylabel('Actual Values')
    plt.title('Actual vs Predicted Values')
    plt.grid(True)
    plt.show()


def draw_avg_values_of_preds():
    pred_path = "./data/prediction_errs_0561-2.txt"
    y_pred_t = np.loadtxt(pred_path)
    y_pred = y_pred_t.T

    avg_values = []

    for i in range(len(y_pred)):
        avg = 0
        for j in range(len(y_pred[i])):
            avg += y_pred[i][j]

        avg = avg/len(y_pred[i])
        avg_values.append(avg)

    plt.plot(avg_values)
    plt.xlabel('Prediction Reach')
    plt.ylabel('Error')
    plt.title("Average Errors")
    plt.grid(True)
    plt.show()

def draw_errors_vs_predicted_value():
    pred_errs_path = "./data/prediction_errs_0561-2.txt"
    y_pred_errs_t = np.loadtxt(pred_errs_path)
    y_pred_errs = y_pred_errs_t.T

    pred_path = "./data/prediction_errs_y_pred0561-2.txt"
    y_pred_t = np.loadtxt(pred_path)
    y_pred = y_pred_t.T

    for i in range(len(y_pred)):
        if i % 10 == 0:
            plt.scatter(y_pred[i], y_pred_errs[i], label="Prediction Time: " + str(i+1))


    plt.legend()
    plt.xlabel("Predicted Values")
    plt.ylabel("Error")

    plt.grid(True)
    plt.show()



draw_errors_vs_predicted_value()
