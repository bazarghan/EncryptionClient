SERVER_URL = 'http://localhost:8000'

# Plant State Space
AP = [[0.99998, 0.0197], [-0.0197, 0.97025]]
BP = [[0.0000999], [0.0098508]]
CP = [[1, 0]]
DP = [[0]]

# Controller State Space
AC = [[1, 0.0063], [0, 0.3678]]
BC = [[0], [0.0063]]
CC = [[10, -99.90]]
DC = [[3]]


