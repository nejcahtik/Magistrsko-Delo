import numpy as np

def remove_prediction_ctr(x, pcn):
    y = x.pop(pcn)
    return x, y



x = {"kurac": "abc",
     "picka": "def"}

x, y = remove_prediction_ctr(x, "kurac")

print(x)
print(y)