import tenseal as ts
import utils
import requests
import base64
import numpy as np
from matplotlib import pyplot as plt
import tqdm
import time

url = 'http://45.11.93.9:8000/tenseal-fully/'
xc = [0, 0]
r = 0


def to_server(y):
    global xc
    context = ts.context_from(utils.read_data('public_key.txt'))
    error = [r - y]
    encrypted_states = ts.ckks_vector(context, xc)
    encrypted_error = ts.ckks_vector(context, error)
    files = {
        'states': base64.b64encode(encrypted_states.serialize()),
        'error': base64.b64encode(encrypted_error.serialize()),
    }
    response = requests.post(url + 'input-controller/', files=files)
    if response.status_code == 200:
        raw_states = response.json()["states"]
        raw_control_signal = response.json()["control_signal"]
    else:
        print(f'error{response.text}')
        exit(0)

    states_proto = base64.b64decode(raw_states.encode('ascii'))
    context = ts.context_from(utils.read_data('secret_key.txt'))
    encrypted_states = ts.lazy_ckks_vector_from(states_proto)
    encrypted_states.link_context(context)

    control_signal_proto = base64.b64decode(raw_control_signal.encode('ascii'))
    encrypted_control_signal = ts.lazy_ckks_vector_from(control_signal_proto)
    encrypted_control_signal.link_context(context)

    xc = np.array(encrypted_states.decrypt())
    control_command = np.array(encrypted_control_signal.decrypt())

    return control_command


AP = np.array([[0.99998, 0.0197], [-0.0197, 0.97025]])
BP = np.array([[0.0000999], [0.0098508]])
CP = np.array([[1, 0]])
DP = np.array([[0]])

xp = np.array([[1], [0]])
y = 0

ys = []
us = []
start = 0
end = 100
Ts = 0.5

times = np.arange(start, end + Ts, Ts)
n = len(times)
real_times = []

for i in tqdm.tqdm(range(n)):
    start = time.time()
    u = to_server(y)
    real_times.append(time.time() - start)
    xp = AP @ xp + BP @ u
    yp = CP @ xp + DP @ u
    y = yp[0, 0]
    ys.append(y)
    us.append(u)

plt.figure()
plt.plot(times, ys)
plt.xlim([0, 100])
plt.show()

plt.figure()
plt.hist(real_times, bins=30)
plt.show()
