def swap_and_scale(a, b, factor):
    return b * factor, a * factor

if __name__ == '__main__':
    print(swap_and_scale(10, 20, 2))
