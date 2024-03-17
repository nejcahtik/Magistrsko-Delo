from datetime import datetime as dt


a = []
start_time = dt.now()
for i in range(28000):
    a.append(i)
end_time = dt.now()

print("execution time: " + str(end_time - start_time))
print(a)