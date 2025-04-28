
def read_bytes_from_waveform(file_path):
    all_bytes = []

    with open(file_path, "r") as file:
        for line in file:
            if "=" in line:
                hex_data = line.split("=")[-1].strip().replace(" ", "")
                # Break into bytes (2 hex chars), LSB first
                bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
                bytes_list.reverse()  # LSB first
                all_bytes.extend(bytes_list)

    return all_bytes


def read_bytes_from_systemC(file_path):
    all_bytes = []

    with open(file_path, "r") as file:
        for line in file:
            cleaned = line.strip().replace(" ", "")
            if cleaned:  # skip empty lines
                all_bytes.append(cleaned)

    return all_bytes

def read_bytes_from_hw_output_txt(file_path):
    all_bytes = []

    with open(file_path, "r") as file:
        for line in file:
            values = line.strip().split()
            for hex_pair in values:
                msb = hex_pair[:2]
                lsb = hex_pair[2:]
                # all_bytes.append(int(lsb, 16))
                # all_bytes.append(int(msb, 16))
                all_bytes.append(lsb)
                all_bytes.append(msb)
    return all_bytes


# Compare the two lists
def compare_data(data1, data2, name):
    if len(data1) != len(data2):
        print(f"Length mismatch in {name}: {len(data1)} vs {len(data2)}")
        # return False
    for i in range(len(data1)):
        if data1[i] != data2[i]:
            print(f"Mismatch in {name} at index {i}: {data1[i]} vs {data2[i]}")
            # return False
    print(f"{name} match!")
    # return True



if __name__ == "__main__":
    input_data_mu_in = read_bytes_from_waveform("/aha/garnet/tests/test_app/input_data_mu_in.txt")
    weight_data_mu_in = read_bytes_from_waveform("/aha/garnet/tests/test_app/weight_data_mu_in.txt")
    bias_data_mu_in = read_bytes_from_waveform("/aha/garnet/tests/test_app/bias_data_mu_in.txt")
    inputScale_data_mu_in = read_bytes_from_waveform("/aha/garnet/tests/test_app/inputScale_data_mu_in.txt")
    weightScale_data_mu_in = read_bytes_from_waveform("/aha/garnet/tests/test_app/weightScale_data_mu_in.txt")

    systolic_array_data_out = read_bytes_from_waveform("/aha/garnet/tests/test_app/systolic_array_output.txt")
    print(len(systolic_array_data_out))


    input_data_systemC = read_bytes_from_systemC("/aha/network_params/input_data_systemC.txt")
    weight_data_systemC = read_bytes_from_systemC("/aha/network_params/weight_data_systemC.txt")
    bias_data_systemC = read_bytes_from_systemC("/aha/network_params/bias_data_systemC.txt")
    inputScale_data_systemC = read_bytes_from_systemC("/aha/network_params/inputScale_data_systemC.txt")
    weightScale_data_systemC = read_bytes_from_systemC("/aha/network_params/weightScale_data_systemC.txt")

    glb_hw_output = read_bytes_from_hw_output_txt("/aha/garnet/tests/test_app/hw_output.txt")


    compare_data(input_data_mu_in, input_data_systemC, "input_data")
    compare_data(weight_data_mu_in, weight_data_systemC, "weight_data")
    compare_data(bias_data_mu_in, bias_data_systemC, "bias_data")
    compare_data(inputScale_data_mu_in, inputScale_data_systemC, "inputScale_data")
    compare_data(weightScale_data_mu_in, weightScale_data_systemC, "weightScale_data")

    compare_data(systolic_array_data_out, glb_hw_output, "systolic_array_output")





