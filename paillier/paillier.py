import random
import sys
import requests
from miller import find_prime, random_number
from base64 import b64encode, b64decode
from constant import SERVER_URL
sys.setrecursionlimit(10 ** 5)


def funcL(x, n):
    return (x - 1) // n


def string_to_number(s):
    return int.from_bytes(s.encode(), 'big')


def number_to_string(num):
    return num.to_bytes((num.bit_length() + 7) // 8, 'big').decode()


def public_key_to_pem(public_key):
    url = f'{SERVER_URL}/setpbk/?public_key={public_key[0]},{public_key[1]}'

    response = requests.get(url)
    if response.status_code != 200:
        print("There is an Error in Setting the Server Public Key")
        exit(0)

    public_key_data = f"{public_key[0]},{public_key[1]}".encode('utf-8')
    b64_encoded_key = b64encode(public_key_data).decode('utf-8')
    line_length = 64
    b64_encoded_key_lines = [b64_encoded_key[i:i + line_length] for i in range(0, len(b64_encoded_key), line_length)]
    formatted_key = '\n'.join(b64_encoded_key_lines)
    pem_key = f"-----BEGIN PAILLIER PUBLIC KEY-----\n{formatted_key}\n-----END PAILLIER PUBLIC KEY-----"

    return pem_key


def private_key_to_pem(private_key):
    private_key_data = f"{private_key[0]},{private_key[1]}".encode('utf-8')
    b64_encoded_key = b64encode(private_key_data).decode('utf-8')
    line_length = 64
    b64_encoded_key_lines = [b64_encoded_key[i:i + line_length] for i in range(0, len(b64_encoded_key), line_length)]
    formatted_key = '\n'.join(b64_encoded_key_lines)
    pem_key = f"-----BEGIN PAILLIER PRIVATE KEY-----\n{formatted_key}\n-----END PAILLIER PRIVATE KEY-----"
    return pem_key


def pem_to_public_key(pem_key):
    header = "-----BEGIN PAILLIER PUBLIC KEY-----"
    footer = "-----END PAILLIER PUBLIC KEY-----"
    pem_key = pem_key.replace(header, '').replace(footer, '').strip()
    b64_encoded_key = ''.join(pem_key.split())
    public_key_data = b64decode(b64_encoded_key).decode('utf-8')
    n, g = map(int, public_key_data.split(','))

    return n, g


def pem_to_private_key(pem_key):
    header = "-----BEGIN PAILLIER PRIVATE KEY-----"
    footer = "-----END PAILLIER PRIVATE KEY-----"
    pem_key = pem_key.replace(header, '').replace(footer, '').strip()
    b64_encoded_key = ''.join(pem_key.split())
    public_key_data = b64decode(b64_encoded_key).decode('utf-8')
    lamb, mui = map(int, public_key_data.split(','))

    return lamb, mui


class Encryption:

    def __init__(self, security=256, generate=False):
        self.g = None
        self.n = None
        self.lamb = None
        self.mui = None
        if generate:
            a = random_number(security, 2)
            search_range = random_number(64, 2)
            b = random_number(security, 2)
            self.p = find_prime(a, a + search_range)
            self.q = find_prime(b, b + search_range)
            self.keyGen()
        else:
            with open('pub.crt', 'r') as f:
                pem_public_key = f.read()
            self.n, self.g = pem_to_public_key(pem_public_key)
            with open('private.crt', 'r') as f:
                pem_private_key = f.read()
            self.lamb, self.mui = pem_to_private_key(pem_private_key)

    def pow_mod(self, a, n, mod):
        if n == 0:
            return 1
        mya = self.pow_mod(a, n // 2, mod)
        d = (mya * mya) % mod
        if n % 2 == 1:
            d = (d * a) % mod
        return d

    def gcd(self, a, b):
        if b == 0:
            return 1, 0, a

        x1, y1, g = self.gcd(b, a % b)
        return y1, x1 - y1 * (a // b), g

    def lcm(self, a, b):
        _, _, g = self.gcd(a, b)
        return (a * b) // g

    def generateSample(self, n):
        a = 2 ** 16 + 1
        _, _, d = self.gcd(a, n)
        while d != 1:
            a = random.randint(1, 2 ** 64)
            _, _, d = self.gcd(a, n)
        return a

    def keyGen(self):
        p = self.p
        q = self.q
        lamb = self.lcm(p - 1, q - 1)
        n = p * q
        g = self.generateSample(n)
        f = funcL(self.pow_mod(g, lamb, n * n), n)
        _, _, d = self.gcd(f, n)
        while d != 1:
            g = self.generateSample(n)
            f = funcL(self.pow_mod(g, lamb, n * n), n)
            _, _, d = self.gcd(f, n)

        mui, _, _ = self.gcd(f, n)
        self.g = g
        self.n = n
        self.lamb = lamb
        self.mui = mui

        pem_private_key = private_key_to_pem([self.lamb, self.mui])
        with open('private.crt', 'w') as f:
            f.write(pem_private_key)

        pem_public_key = public_key_to_pem([self.n, self.g])
        with open('pub.crt', 'w') as f:
            f.write(pem_public_key)

    def publicKey(self):
        return self.n, self.g

    def privateKey(self):
        return self.lamb, self.mui

    def encrypt(self, m, pub1=None, pub2=None):
        if pub1 is None:
            pub1 = self.n
        if pub2 is None:
            pub2 = self.g

        n2 = pub1 * pub1
        r = random.randint(1, pub1)
        return (self.pow_mod(pub2, m, n2) * self.pow_mod(r, pub1, n2)) % n2

    def encrypt_mat(self, A):
        result = [[0 for _ in range(len(A[0]))] for _ in range(len(A))]
        for i in range(len(A)):
            for j in range(len(A[0])):
                result[i][j] = self.encrypt(A[i][j])
        return result

    def decrypt(self, c, pv1=None, pv2=None, pub1=None):
        if pv1 is None:
            pv1 = self.lamb
        if pv2 is None:
            pv2 = self.mui
        if pub1 is None:
            pub1 = self.n

        n2 = pub1 * pub1
        return (funcL(self.pow_mod(c, pv1, n2), pub1) * pv2) % pub1

    def decrypt_mat(self, A):
        result = [[0 for _ in range(len(A[0]))] for _ in range(len(A))]
        for i in range(len(A)):
            for j in range(len(A(0))):
                result[i][j] = self.decrypt(A[i][j])
        return result


def main():
    my_encryption = Encryption()
    a = 5783
    b = -100
    g, n = my_encryption.publicKey()
    b += n
    b = (b + n) % n
    ae = my_encryption.encrypt(a)
    be = my_encryption.encrypt(b)
    n2 = n * n
    res, _, _ = my_encryption.gcd(ae, n2)
    print(((my_encryption.decrypt(ae * be) + n // 2) % n) - n // 2)


if __name__ == "__main__":
    main()
