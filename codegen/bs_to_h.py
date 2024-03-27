# script to convert bitstream to h file

def convert_bs(bs_file_name, new_name):

    bs_lines = []
    bs_file_str = new_name

    with open(bs_file_name) as bs_file:
        for bs_line in bs_file:
            bs_lines.append(bs_line)

    f = open(bs_file_str+"script.h", "w")
    # defines
    f.write("#ifndef BITSTREAM_H\n")
    f.write("#define BITSTREAM_H\n\n")
    f.write("const int app_size = " + str(len(bs_lines)) + ";\n\n")

    # addr array
    f.write("uint32_t app_addrs_script[] = {\n")
    for line in bs_lines:
        strings = line.split()
        f.write("  0x" + strings[0] + ",\n")
    f.write("};\n\n")


    # data array
    f.write("uint32_t app_datas_script[] = {\n")
    for line in bs_lines:
        strings = line.split()
        f.write("  0x" + strings[1] + ",\n")
    f.write("};\n\n")

    # defines
    f.write("#endif  // BITSTREAM_H\n")


if __name__ == '__main__':
    convert_bs(bs_file_name, new_name)
