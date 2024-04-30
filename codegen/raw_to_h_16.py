# script to convert bitstream to h file

import itertools


def convert_image(input_data, output_data, data_file_str, num_tiles, dense):

    raw_input_data_list = []
    raw_input_data_size_list = []
    raw_output_data_list = []
    raw_output_data_size_list = []

    for input in input_data:
        with open(data_file_str + input, "rb") as f:
            raw = f.read()
        raw = [hex(c) for c in raw]

        raw1 = raw[0::2]
        raw2 = raw[1::2]
        raw_image0 = []

        for (raw_i, raw_j) in itertools.zip_longest(raw1, raw2):
            raw_j = raw_j[2:]
            if(len(raw_j) == 1):
                raw_j = '0'+ raw_j
            raw_final = raw_i + raw_j
            raw_image0.append(raw_final)

        raw2 = raw_image0 

        length_input_data = len(raw2)
        raw_input_data_size_list.append(length_input_data)
        raw_input_data = ', '.join(raw2)
        raw_input_data_list.append(raw_input_data)

    if dense:
        for output in output_data:

            with open(data_file_str + output, "rb") as f:
                raw = f.read()
            raw = [hex(c) for c in raw]

            raw1 = raw[0::2]
            raw2 = raw[1::2]
            raw_image0 = []

            for (raw_i, raw_j) in itertools.zip_longest(raw1, raw2):
                raw_j = raw_j[2:]
                if(len(raw_j) == 1):
                    raw_j = '0'+ raw_j
                raw_final = raw_i + raw_j
                raw_image0.append(raw_final)

            raw2 = raw_image0 

            length_output_data = len(raw2)
            raw_output_data_size_list.append(length_output_data)
            raw_output_data = ', '.join(raw2)
            raw_output_data_list.append(raw_output_data)


    f = open("./input_script.h", "w")

    f.write(f"int runs = {num_tiles};\n")

    for idx, input in enumerate(input_data):
        input_str = input.replace("hw_", "")
        input_str = input_str.replace(".raw", "")
        # If using sections.ld
        # f.write(f"uint16_t app_{input_str}_data[] __attribute__((section(\".app_{input_str}_data\"))) = {{ \n")
        f.write(f"uint16_t app_{input_str}_data[] = {{ \n")
        f.write(raw_input_data_list[idx])
        f.write("\n};\n")
        f.write(f"const unsigned int app_{input_str}_data_size =  " + str(raw_input_data_size_list[idx]) +  ";\n")

    if dense: 
        for idx, output in enumerate(output_data):
            output_str = output.replace("hw_", "")
            output_str = output_str.replace(".raw", "")
            f.write(f"uint16_t app_{output_str}_data[] = {{ \n")
            f.write(raw_output_data_list[idx])
            f.write("\n};\n")
            f.write(f"const unsigned int app_{output_str}_data_size =  " + str(raw_output_data_size_list[idx]) +  ";\n")

        
    f.close

if __name__ == '__main__':
    convert_image(input_data, output_data, num_tiles, dense)
