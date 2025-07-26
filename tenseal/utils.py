import base64


def write_data(filename: str, data: bytes):
    data = base64.b64encode(data)
    with open(filename, 'wb') as f:
        f.write(data)
        f.close()


def read_data(filename: str) -> bytes:
    with open(filename, 'rb') as f:
        data = f.read()
        f.close()
    return base64.b64decode(data)
