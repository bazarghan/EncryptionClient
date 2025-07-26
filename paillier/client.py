import json
from constant import SERVER_URL, AP, AC, BP, BC, CP, CC, DC, DP, INITIAL_COND
import numpy as np
import requests
import matplotlib.pyplot as plt
import time
from ss import StateSpace as ss, MED
from paillier import Encryption


def create_controller(c_encoder):
    Ae = c_encoder.encode(np.array(AC))
    Be = c_encoder.encode(np.array(BC))
    Ce = c_encoder.encode(np.array(CC))
    De = c_encoder.encode(np.array(DC))

    encrypted_initial_value = Enc.encrypt_mat(initial_value)

    payload = {
        "A": Ae,
        "B": Be,
        "C": Ce,
        "D": De,
        "init": encrypted_initial_value,
        "n": 2,
    }

    url = f"{SERVER_URL}/create-controller/"
    json_payload = json.dumps(payload)
    response = requests.post(url, data=json_payload)

    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        exit(0)


def input_controller(r1_inp, r2_inp):
    my_url = f"{SERVER_URL}/input-controller/?inputs={r1_inp},{r2_inp}"
    res = requests.get(my_url)
    outputs = res.json().get("outputs")
    return outputs


def reset_controller():
    my_url = f"{SERVER_URL}/reset-controller/"
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
    flag = False
    for r in tf_input:
        error = r - out
        error_encode = sim_encoder.encode(error, iteration)
        error_enc = encryption_sim.encrypt(error_encode)
        error_check = 0
        error_check_encode = sim_encoder.encode(error_check, iteration)
        error_check_enc = encryption_sim.encrypt(error_check_encode)
        inp_result = input_controller(error_enc, error_check_enc)
        out_enc = inp_result[0]
        if not flag:
            print(encryption_sim.decrypt(inp_result[1]))
            flag = True
        out_dec = encryption_sim.decrypt(out_enc)
        out_decode = sim_encoder.decode(out_dec, iteration + 1)

        out = Gp.out(out_decode)
        end_time = time.time()
        time_sim.append(end_time - start_time)
        output.append(out)
        iteration += 1
        if iteration == 5:
            iteration = 1
            reset_controller()

    return output, time_sim


plant = ss(
    np.array(AP), np.array(BP), np.array(CP), np.array(DP), np.array(INITIAL_COND)
)
controller = ss(np.array(AC), np.array(BC), np.array(CC), np.array(DC))

# Encrypted Control statespace
Enc = Encryption(512, True)
n, g = Enc.publicKey()

encoder = MED(n, 1000)

initial_value = encoder.encode(np.zeros((2, 1)))

create_controller(encoder)

uc = 1
r_encode = encoder.encode(uc)
r_enc = Enc.encrypt(r_encode)

start = 0
end = 5
ts = 0.01
length = int((end - start) / ts)
t = np.linspace(start, end, length)
u = [0] * length
y = sim(u, controller, plant)
plant.reset()
y_enc, time_enc = sim_enc(u, plant, encoder, Enc)


plt.figure()
plt.plot(t, y)
plt.step(time_enc, y_enc)
plt.plot(t, u, linestyle="--")
plt.xlim([start, end])

plt.legend(["Output (y)", "Encrypted Output (y_enc)", "Input (u)"])
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.title("System Response")

plt.show()

time_data = []
for i in range(1, len(time_enc)):
    time_data.append(time_enc[i] - time_enc[i - 1])


plt.figure()
plt.hist(time_data, bins=30, edgecolor="black")

plt.title("Histogram of Control Sample time")
plt.xlabel("Time Samples")
plt.ylabel("Frequency")
plt.show()
