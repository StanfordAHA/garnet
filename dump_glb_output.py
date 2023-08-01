import os
import sys

def dump_files_to_header(directory, output_file, app_name, line_length=80):
    files = [file for file in os.listdir(directory) if file.startswith('tensor_X') and file.endswith('.txt')]
    print(files)
    files.sort()
    print(files)
    with open(output_file, 'w') as header_file:
        header_file.write(f'#ifndef _{app_name.upper()}_H\n')
        header_file.write(f'#define _{app_name.upper()}_H\n\n')
        header_file.write('#include <stdint.h>\n\n')

        for file_name in files:
            mode = file_name.split('_')[3]  # format is "tensor_X_mode_<mode>.txt"
            array_name = f'app_tensor_X_mode_{mode}_0_data'
            array_name = array_name.replace('.txt', '')
            header_file.write(f'extern const uint16_t {array_name}[];\n')

        header_file.write(f'\n\n')
        

    with open(output_file, 'a') as header_file:
        for file_name in files:
            mode = file_name.split('_')[3]  
            array_name = f'app_tensor_X_mode_{mode}_0_data'
            array_name = array_name.replace('.txt', '')
            header_file.write(f'uint16_t {array_name}[] = {{\n\t')
            with open(os.path.join(directory, file_name), 'r') as file:
                lines = [line.strip() for line in file.readlines()]

                hex_values = []
                lastvalue = 0
                for line in lines:
                    values = line.split()
                    while values and values[-1] == '0000' and (len(values) == 1 or values[-2] == '0000'):
                        values.pop()
                    hex_values.extend([value for value in values])
                del hex_values[-1]

                # write nicely on single line
                current_line_length = 0
                if (hex_values):
                    # print(hex_values)
                    for index, hex_value in enumerate(hex_values):
                        value_length = len(hex_value) + 4  
                        if current_line_length + value_length > line_length:
                            header_file.write('\n\t')
                            current_line_length = 4 
                        header_file.write(f'0x{hex_value}')
                        if index < len(hex_values) - 1:
                            header_file.write(',')
                        current_line_length += value_length
                header_file.write('\n};\n\n')

            array_size_name = f'{array_name}_size'
            header_file.write(f'const unsigned int {array_size_name} = {len(hex_values)};\n\n')
        
        header_file.write('\n#endif\n')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python3 dump_glb_output.py <app_name>')
        sys.exit(1)
    
    directory = '/aha/garnet/tests/test_app'
    app_name = sys.argv[1]
    output_file = f'{app_name}.h'
    dump_files_to_header(directory, output_file, app_name, line_length=80)
