from textwrap import dedent
import parse_gold


def unrolling(inputs, outputs, input_place_list, output_place_list, extent_dict, name_list, dense, app_name):
    f = open("./unrolling.h", "w")
    checkpoint = 0
    f.write("#include \"glb.h\"\n")
    print(output_place_list)
    flat_list = [item for sublist in output_place_list for item in sublist]
    output_binary_string = "1" *len(flat_list)
    print(output_binary_string)
    f.write(f"int output_mask = 0b{output_binary_string};")

    for idx, input_name in enumerate(inputs):
        input_name_str = input_name.replace("hw_", "")
        input_name_str = input_name_str.replace(".raw", "")
        input_str = ", ".join([str(elem) for elem in input_place_list[idx]])

        if("matmul_ijk" in app_name):
            if ("mode_0" in input_name_str and "tensor_C" in input_name_str):
                input_name_str = input_name_str.replace("mode_0", "mode_1")
            elif ("mode_1" in input_name_str and "tensor_C" in input_name_str):
                input_name_str = input_name_str.replace("mode_1", "mode_0")

        f_str = f'''
        int {input_name_str}_unroll = {len(input_place_list[idx])};
        int {input_name_str}_unroll_array[{len(input_place_list[idx])}] = {{{input_str}}};
        '''
        f.write(dedent(f_str))
    
    f.write("\n")
    
    for idx, input_name in enumerate(inputs):
        extents = extent_dict[input_name]
        input_name_str = input_name.replace("hw_", "")
        input_name_str = input_name_str.replace(".raw", "")
        input_str = ", ".join([str(elem) for elem in extents])
        f_str = f'''
        int {input_name_str}_extents[{len(extents)}] = {{{input_str}}};
        '''
        f.write(dedent(f_str))

    f.write("\n")

    f.write("static void move_input_data(){")
    for idx, input_name in enumerate(inputs):
        input_name_str = input_name.replace("hw_", "")
        input_name_str = input_name_str.replace(".raw", "")
        f_str = f'''
        for (int i = 0; i < {input_name_str}_unroll; i++) {{
          write_glb_memory(0x40000 * ({input_name_str}_unroll_array[i]), (uint16_t * ) app_{input_name_str}_data, app_{input_name_str}_data_size / {input_name_str}_unroll, i, {input_name_str}_unroll);
        }}
        '''
        f.write(dedent(f_str))
        checkpoint = checkpoint + len(input_place_list[idx])
    f.write("}\n\n")

    # stream val calculations
    stream_pulse_g2f = 0
    stream_pulse_f2g = 0

    f.write("\n")

    for io_in in input_place_list:
      stream_pulse_g2f |= (1 << io_in[0])
    for io_out in output_place_list:
      stream_pulse_f2g |= (1 << io_out[0])

    f.write(f"int stream_pulse_g2f = {hex(stream_pulse_g2f)};\n")
    f.write(f"int stream_pulse_f2g = {hex(stream_pulse_f2g)};\n\n")

    f.write("static void update_glb_pointer_start_addr(int k){")
    for idx, input_name in enumerate(inputs):
        input_name_str = input_name.replace("hw_", "")
        input_name_str = input_name_str.replace(".raw", "")
        f_str = f'''        
        for (int i = 0; i < {input_name_str}_unroll; i++) {{
          int sum = 0;
          if (k == 0) {{
            sum = {input_name_str}_extents[k]*2;
          }} else {{
            sum = {input_name_str}_extents[k]*2 + {input_name_str}_extents[k-1]*2;
            {input_name_str}_extents[k] = sum/2;
          }}
        HAL_Cgra_Glb_WriteReg(0x100 * ({input_name_str}_unroll_array[i]) + GLB_LD_DMA_HEADER_0_START_ADDR_R, 0x40000 * ({input_name_str}_unroll_array[i]) + sum);
        }}
        '''
        f.write(dedent(f_str))

    f.write("}\n\n")

    f.write("\n")

    f.write("static void update_glb_pointer_extent(int k){")
    for idx, input_name in enumerate(inputs):
        input_name_str = input_name.replace("hw_", "")
        input_name_str = input_name_str.replace(".raw", "")
        f_str = f'''
        for (int i = 0; i < {input_name_str}_unroll; i++) {{
          HAL_Cgra_Glb_WriteReg(0x100 * ({input_name_str}_unroll_array[i]) + GLB_LD_DMA_HEADER_0_RANGE_0_R, {input_name_str}_extents[k]-2);
        }}
        '''
        f.write(dedent(f_str))

    f.write("}\n\n")

    f.write("\n")


    if dense: 
      for idx, output_name in enumerate(outputs):
          output_name_str = output_name.replace("hw_", "")
          output_name_str = output_name_str.replace(".raw", "")
          f.write(f"int {output_name_str}_banks = {len(output_place_list[idx])};\n")
          f.write(f"int {output_name_str}_bank_array[{len(output_place_list[idx])}] = {{\n")
          output_place = ", ".join([str(elem) for elem in output_place_list[idx]])
          f.write(output_place)
          f.write(f"\n}};\n")

      f.write("static int check_gold_data()\n")
      f.write("{\n")
      f.write("int err = 0;\n")
      for idx, output_name in enumerate(outputs):
          output_name_str = output_name.replace("hw_", "")
          output_name_str = output_name_str.replace(".raw", "")
          f.write(f"for (int b = 0; b < {output_name_str}_banks; b++){{\n")
          f.write(f"    int bank = {output_name_str}_bank_array[b];\n")
          f.write(f"    uint16_t * read_base = AHASOC_CGRA_DATA_BASE + 0x20000 + bank*0x40000;\n")
          f.write(f"    for (int i = 0; i < app_{output_name_str}_data_size/{output_name_str}_banks; i++) {{\n")
          f.write(f"        if ((uint16_t)(read_base[i]) != (uint16_t) app_{output_name_str}_data[i*{output_name_str}_banks+b]) {{\n")
          f.write(f"        err++;\n")
          f.write(f"        printf(\"index %d\\n\", i);\n")
          f.write(f"        printf(\"output_data %lx\\n\", read_base[i]);\n")
          f.write(f"        printf(\"gold_data %lx\\n\", app_{output_name_str}_data[i*{output_name_str}_banks+b]);\n")
          f.write(f"        }}\n")
          f.write(f"    }}\n")
          f.write(f"}}\n")
      f.write("return err;\n")
      f.write("}\n\n")

    else:
        print("no gold")
        #parse_gold.parse_gold(f, name_list)
      


if __name__ == '__main__':
    unrolling(inputs, outputs, input_place_list, output_place_list, extent_dict, name_list, dense, app_name)

