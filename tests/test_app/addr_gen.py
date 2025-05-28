# Y1 = 2
# X1 = 2
# K1 = 8
# Y0 = 7
# X0 = 7
# K0 = 32




def get_address(y1, x1, k1, y0, x0):
    y = y1 * Y0 + y0
    x = x1 * X0 + x0
    k = k1 * K0

    addr = y * (X1 * X0 * K1 * K0) + x * (K1 * K0) + k
    return addr


def print_addr_map():
    for y1 in range(0, Y1):
        for x1 in range(0, X1):
            for k1 in range(0, K1):
                for y0 in range(0, Y0):
                    for x0 in range(0, X0):
                        addr = get_address(y1, x1, k1, y0, x0)
                        print(f"addr: {addr}, bank index: {int(addr/32)}, y1: {y1}, x1: {x1}, k1: {k1}, y0: {y0}, x0: {x0}")




if __name__ == "__main__":
    Y1 = 4
    X1 = 8
    K1 = 2
    Y0 = 14
    X0 = 7
    K0 = 32

    # print_addr_map()

    dX0 = K1 * K0
    dY0 = (get_address(0, 0, 0, 1, 0) - get_address(0, 0, 0, 0, X0 - 1))/32
    dK1 = (get_address(0, 0, 1, 0, 0) - get_address(0, 0, 0, Y0 - 1, X0 - 1))/32
    dX1 = (get_address(0, 1, 0, 0, 0) - get_address(0, 0, K1 - 1, Y0 - 1, X0 - 1))/32
    dY1 = (get_address(1, 0, 0, 0, 0) - get_address(0, X1 - 1, K1 - 1, Y0 - 1, X0 - 1))/32

    # Print all the derivatives in one line
    print(f"dX0: {dX0}, dY0: {dY0}, dK1: {dK1}, dX1: {dX1}, dY1: {dY1}")



