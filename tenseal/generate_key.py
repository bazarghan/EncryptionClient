import tenseal as ts
import utils
import requests

context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60]
)

context.global_scale = 2 ** 40
context.generate_galois_keys()
secret_context = context.serialize(save_secret_key=True)
utils.write_data('secret_key.txt', secret_context)
context.make_context_public()
public_key = context.serialize()
utils.write_data('public_key.txt', public_key)

with open('public_key.txt', 'rb') as f:
    file = f.read()
files = {'file': file}

url = 'http://localhost:8000/tenseal-fully/'
response = requests.post(url + 'setpbk/', files=files)
if response.status_code == 200:
    print('Key Generation and public key setting was successful!!')
else:
    print(f"Error: {response.text}")
