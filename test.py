from datetime import datetime as dt
import math
import matplotlib.pyplot as plt

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


draw_graph()