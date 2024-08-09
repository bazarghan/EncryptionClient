import json
from constant import SERVER_URL, AP, AC, BP, BC, CP, CC, DC, DP, INITIAL_COND
import numpy as np
import requests
import matplotlib.pyplot as plt
import time
from ss import StateSpace as ss, MED
from paillier import Encryption


def input_controller(r_inp):
    my_url = f'{SERVER_URL}/input-controller/?inputs={r_inp}'
    res = requests.get(my_url)
    outputs = res.json().get('outputs')
    return outputs


def reset_controller():
    my_url = f'{SERVER_URL}/reset-controller/'
    res = requests.get(my_url)
    if res.status_code == 200:
        return True
    else:
        print("There is Error in Resetting Controller!!")
        exit(0)


def sim(tf_input, G1, G2):
    output = []
    out = 0
    for r in tf_input:
        error = r - out
        out = G2.out(G1.out(error))
        output.append(out)
    return output


def sim_enc(tf_input, Gp, sim_encoder, encryption_sim):
    output = []
    time_sim = []
    out = 0
    iteration = 1

    start_time = time.time()
    for r in tf_input:

        error = r - out
        error_encode = sim_encoder.encode(error, iteration)
        error_enc = encryption_sim.encrypt(error_encode)

        out_enc = input_controller(error_enc)[0]
        out_dec = encryption_sim.decrypt(out_enc)
        out_decode = sim_encoder.decode(out_dec, iteration + 1)

        out = Gp.out(out_decode)
        end_time = time.time()
        time_sim.append(end_time - start_time)
        output.append(out)
        iteration += 1
        if iteration == 10:
            iteration = 1
            reset_controller()

    return output, time_sim


plant = ss(np.array(AP), np.array(BP), np.array(CP), np.array(DP), np.array(INITIAL_COND))
controller = ss(np.array(AC), np.array(BC), np.array(CC), np.array(DC))

# Encrypted Control statespace
Enc = Encryption(512)
n, g = Enc.publicKey()

encoder = MED(n, 100)

Ae = encoder.encode(np.array(AC))
Be = encoder.encode(np.array(BC))
Ce = encoder.encode(np.array(CC))
De = encoder.encode(np.array(DC))

initial_value = encoder.encode(np.zeros((2, 1)))
encrypted_initial_value = Enc.encrypt_mat(initial_value)

payload = {
    'A': Ae, 'B': Be, 'C': Ce, 'D': De, 'init': encrypted_initial_value, 'n': 1
}

url = f'{SERVER_URL}/create-controller/'
json_payload = json.dumps(payload)
response = requests.post(url, data=json_payload)

if response.status_code == 200:
    data = response.json()  # If the response is JSON
else:
    print(f"Request failed with status code {response.status_code}")
    exit(0)

uc = 1
r_encode = encoder.encode(uc)
r_enc = Enc.encrypt(r_encode)

start = 0
end = 20
ts = 0.1
length = int((end - start) / ts)
t = np.linspace(start, end, length)
u = [0] * length
y = sim(u, controller, plant)
plant.reset()
y_enc, time_enc = sim_enc(u, plant, encoder, Enc)

plt.plot(t, y)
plt.step(time_enc, y_enc)
plt.plot(t, u, linestyle='--')
plt.xlim([start, end])

plt.show()
