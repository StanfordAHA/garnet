import math
import struct
import numpy as np

import torch
import torch.nn.functional as F


def read_tensor(filename, tensor_shape):
    with open(filename, 'rb') as f:
        file_content = f.read()

    num_elements = len(file_content) // struct.calcsize('f')
    print(f"INFO: Read {num_elements} elements from binary file {filename}")
    unpacked_data = struct.unpack(f'{num_elements}f', file_content)

    tensor = torch.tensor(unpacked_data).reshape(tensor_shape)
    return tensor


def float_to_e8m0(x):
    # Assume input is a float32 tensor
    x = x.cpu().numpy().astype(np.float32)
    bits = np.frombuffer(x.tobytes(), dtype=np.uint32)
    e8m0 = ((bits >> 23) & 0xFF)  # extract exponent only
    return e8m0


def float32_to_bfloat16_bits(x):
    # Step 1: Move to CPU and convert to NumPy float32
    np_fp32 = x.cpu().numpy().astype(np.float32)

    # Step 2: View as uint32
    np_uint32 = np_fp32.view(np.uint32)

    # Step 3: Extract top 16 bits (bfloat16 format)
    np_bf16_uint16 = (np_uint32 >> 16).astype(np.uint16)

    return np_bf16_uint16


def write_list_to_hex(list, filename):
   #Write the entire tensor in hex format to a new file
   with open(filename, 'w') as output_file:
        for idx in range(len(list)):
            value = list[idx]
            output_file.write(str(f"{value:04x}"))
            # if idx != len(list) - 1:
            #     output_file.write(" ")
            if idx != len(list) - 1:
                output_file.write("\n")

if __name__ == '__main__':
    debug_mode = False

    # LAYER PARAMS
    layer_X = 16
    layer_Y = 16
    layer_IC = 128
    layer_OC = 64
    layer_FX = 3
    layer_FY = 3
    layer_BLOCK_SIZE = 64

    # Base path for the binary files
    base_path = '/aha/network_params_fake_conv2d/'

    # FIXME: These should not be hardcoded
    input_path = base_path + 'getitem_1.bin'
    weight_path = base_path + '_param_constant0_weight_0.bin'
    bias_path = base_path + '_param_constant1.bin'
    inputScale_path = base_path + 'getitem.bin'
    weightScale_path = base_path + '_param_constant0_scale_0.bin'


    input = read_tensor(input_path, (1, layer_IC, layer_Y, layer_X))
    # Re-order it so ic0 is the innermost dimension (Y, X, OC0, IC0)
    input_reordered = input.permute(2, 3, 0, 1)
    input_int8 = input_reordered.to(torch.int8)

    weight = read_tensor(weight_path, (layer_OC, layer_IC, layer_FY, layer_FX))
    # Re-order it so oc0 is the innermost dimension (FY, FX, IC0, OC0)
    weight_reordered = weight.permute(2, 3, 1, 0)
    weight_int8 = weight_reordered.to(torch.int8)

    bias = read_tensor(bias_path, (layer_OC))
    bias_bf16 = float32_to_bfloat16_bits(bias)

    inputScale = read_tensor(inputScale_path, (1, int(layer_IC/layer_BLOCK_SIZE), layer_Y, layer_X))
    # Re-order it so ic0 is the innermost dimension (Y, X, OC0, IC0)
    inputScale_reordered = inputScale.permute(2, 3, 0, 1)
    inputScale_e8m0 = float_to_e8m0(inputScale_reordered)

    weightScale = read_tensor(weightScale_path, (layer_OC, int(layer_IC/layer_BLOCK_SIZE), layer_FY, layer_FX))
    # Re-order it so oc0 is the innermost dimension (FY, FX, IC0, OC0)
    weightScale_reordered = weightScale.permute(2, 3, 1, 0)
    weightScale_e8m0 = float_to_e8m0(weightScale_reordered)

    # conv2x_gold_output = read_tensor('/aha/network_params/conv2d_mx_default.bin', (1, 64, 56, 56))
    # # Re-order it so oc0 is the innermost dimension (Y, X, IC0, OC0)
    # conv2x_gold_output_reordered = conv2x_gold_output.permute(2, 3, 1, 0)
    # conv2x_gold_output_reordered_bf16 = float32_to_bfloat16_bits(conv2x_gold_output_reordered)
    # conv2x_gold_output_reordered_bf16_list = conv2x_gold_output_reordered_bf16.flatten().tolist()

    torch.set_printoptions(precision=10)

    if debug_mode:
        # Print first 10 elements and max value
        print("First 10 elements of the input tensor:", input.flatten()[:10])
        print("Max value of the input tensor:", torch.max(input))

        print("First 10 elements of the input INT8 tensor:", input_int8.flatten()[:10])
        print("Max value of the input INT8 tensor:", torch.max(input_int8))

        print("First 10 elements of the bias tensor:", bias.flatten()[:10])
        print("Max value of the bias tensor:", torch.max(bias))

        print("First 10 elements of the bias bFloat16 tensor:", bias_bf16.flatten()[:10])
        # print("Max value of the bias bFloat16 tensor:", torch.max(bias_bf16))
        print("First 10 elements of the inputScale tensor:", inputScale.flatten()[:10])
        print("Max value of the inputScale tensor:", torch.max(inputScale))
        print("Min value of the inputScale tensor:", torch.min(inputScale))

        print("First 10 elements of the inputScale e8m0 tensor:", inputScale_e8m0.flatten()[:10])

        print("First 10 elements of the weightScale tensor:", weightScale.flatten()[:10])
        print("Max value of the weightScale tensor:", torch.max(weightScale))
        print("Min value of the weightScale tensor:", torch.min(weightScale))

        print("First 10 elements of the weightScale e8m0 tensor:", weightScale_e8m0.flatten()[:10])

        print("First 10 elements of the weight tensor:", weight.flatten()[:10])
        print("Shape of the bytes object:", len(input_int8.numpy().tobytes()))

    output_dir = '/aha/network_params_fake_conv2d/'
    # Create output dir if it doesn't exist
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Write the tensors to hex files
    write_list_to_hex(input_int8.numpy().tobytes(), output_dir + 'input_hex.txt')
    write_list_to_hex(weight_int8.numpy().tobytes(), output_dir + 'weight_hex.txt')
    write_list_to_hex(bias_bf16, output_dir + 'bias_hex.txt')
    write_list_to_hex(inputScale_e8m0, output_dir + 'inputScale_hex.txt')
    write_list_to_hex(weightScale_e8m0, output_dir + 'weightScale_hex.txt')
    # write_list_to_hex(conv2x_gold_output_reordered_bf16_list, '/aha/network_params/conv2x_gold_output_hex.txt')
