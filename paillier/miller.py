import random
import time

start = time.time()
primes = [2, 3, 5]


def pow_mod(a, n, mod):
    a %= mod
    res = 1
    while n > 0:
        if n & 1:
            res = res * a % mod
        a = a * a % mod
        n >>= 1

    return res


def prime(n, iteration=10):
    for pr in primes:
        if n % pr == 0:
            return False

    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1

    while iteration > 0:
        iteration -= 1
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue

        prime_check = False
        for i in range(r - 1):
            x = pow_mod(x, 2, n)
            if x == n - 1:
                prime_check = True
                break
        if prime_check:
            continue
        else:
            return False

    return True


def random_number(k, base=10):
    a = 0
    for i in range(k):
        r = random.randint(0, base - 1)
        if i == 0:
            r = random.randint(1, base - 1)
        a *= base
        a += r
    return a


def find_prime(minimum, maximum):
    for number in range(minimum, maximum):

        if number % 5 * 10 ** 9 == 0:
            print('#', end='', flush=True)

        if prime(number):
            print()
            return number

    return -1


def main():
    number_of_digit = 512
    minimum = random_number(number_of_digit, 2)
    maximum = minimum + random_number(11)
    num1 = find_prime(minimum, maximum)
    minimum = random_number(number_of_digit, 2)
    maximum = minimum + random_number(11)
    num2 = find_prime(minimum, maximum)

    with open("prime.txt", "w") as file:
        file.write("p = " + str(num1) + "\nq = " + str(num2))
        print()
        print("prime number saved in prime.txt")

    end = time.time()
    print(end - start)


if __name__ == "__main__":
    main()
