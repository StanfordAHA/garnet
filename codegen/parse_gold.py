import numpy as np
import os
import glob
from textwrap import dedent
import sys

def parse_gold(app_name, data):

    tilefiles = glob.glob("tiles_chip_test/tile*")
    f = open(f"dot_h_files/{app_name}/{data}/{app_name}_{data}_gold.h", 'w')
    name_list = []
    for i in range(0, len(tilefiles)):
        name_list.append(f"tile{i}")


    counter = 0
    # TODO assumes all tiles are same size and square

    gold_list = []

    for gold in name_list:
        gold_list.append(np.load(f"tiles_chip_test/{gold}/output_gold_0.npy"))
    
    f.write("#define AHASOC_CGRA_DATA_BASE    (0x20400000UL)  /*!< (CGRA DATA ) Base Address */\n")

    for idx, gold in enumerate(gold_list):
        if(not np.any(gold)):
            counter += 1
        
        f_str = f'''
        const uint16_t gold_{idx}_[{gold.shape[0] * gold.shape[1]}] = 
        {{
        '''

        f.write(dedent(f_str))

        
        # print(gold)

        for i in range(gold_list[0].shape[0]):
            for j in range(gold_list[0].shape[0]):
                f.write(f"{gold[i][j]}, ")

        f.write("\n};")

    f_str = f'''
    uint16_t check_0_[{gold.shape[0] * gold.shape[1]}] = 
    {{
    '''

    f.write(dedent(f_str))

    for i in range(gold_list[0].shape[0]):
        for j in range(gold_list[0].shape[0]):
            f.write(f"0, ")

    f.write("\n};\n")


    # TODO assumes dimension of {gold_list[0].shape[0]}, safe to assume all tiles same?

    f_str = f'''
    uint16_t check_gold_data(){{

    uint16_t size; 
    uint16_t err = 0;
    uint16_t mode0_idx = 0;
    uint16_t mode1_idx = 0;
    uint16_t vals_idx = 0;

    const uint32_t read_start_addr = 0x10000;

    uint16_t * read_base = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr);
    uint16_t * read_base2 = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + 0x20000);
    uint16_t * read_base3 = (uint16_t*) (AHASOC_CGRA_DATA_BASE + read_start_addr + 2*0x20000);

    for(uint16_t run = 0; run < runs; run++){{

        uint16_t * gold_ptr;
        uint16_t * check_ptr;
    '''
    f.write(dedent(f_str))


    f.write(dedent(f"       switch(run){{"))
    for idx, gold in enumerate(gold_list):
        f_str = f'''
                    case {idx}:
                        gold_ptr = gold_{idx}_;
                        check_ptr = check_0_;
                        break;
                    '''
        f.write(dedent(f_str))

    f.write(dedent(f'''        
                    default: 
                        // assert(1 == 0);
                        break;}}
            '''))


    f_str = f'''
        size = read_base[mode0_idx];
        uint16_t mode0_size = size + 1 + read_base[mode0_idx + size + 1] + 1;
        uint16_t mode0_stream_size = read_base[mode0_idx + size + 1];
        uint16_t mode0_base = size + 1 + 1;

        size = read_base2[mode1_idx];
        uint16_t mode1_base = size + 1 + 1;
        uint16_t mode1_size = size + 1 + read_base2[mode1_idx + size + 1] + 1;
        
        uint16_t vals_size = read_base3[vals_idx] + 1;

        uint16_t x;
        uint16_t y;
        uint16_t y_dim;
        uint16_t y_idx = 0; 

        // reset check matrix
        for(uint16_t i = 0; i < {gold_list[0].shape[0]}; i++){{
        for(uint16_t j = 0; j < {gold_list[0].shape[0]}; j++){{
            check_ptr[{gold_list[0].shape[0]}*i+j] = 0;
        }}
        }}

        // construct dense matrix
        for(uint16_t i = 0; i < mode0_stream_size; i++){{
        x = read_base[mode0_idx + mode0_base + i];
        y_dim = read_base2[mode1_idx + i + 2] - read_base2[mode1_idx + i + 1];
        for(uint16_t j = 0; j < y_dim; j++){{
            y = read_base2[mode1_idx + mode1_base + y_idx + j];
            check_ptr[{gold_list[0].shape[0]}*x+y] = read_base3[vals_idx + y_idx + j + 1];
        }}
        y_idx += y_dim;
        }}  

        // compare with gold dense matrix
        for(uint16_t i = 0; i < {gold_list[0].shape[0]}; i++){{
        for(uint16_t j = 0; j < {gold_list[0].shape[0]}; j++){{
            if(check_ptr[{gold_list[0].shape[0]}*i+j] != gold_ptr[{gold_list[0].shape[0]}*i+j]){{
            printf(\"error! tile: %d, x: %d y:%d gold_ptr:%d check_ptr:%d\\n\", run, i, j, gold_ptr[{gold_list[0].shape[0]}*i+j], check_ptr[{gold_list[0].shape[0]}*i+j]);
            err++;
            }}
        }}
        }}

        mode0_idx += mode0_size;
        mode1_idx += mode1_size;
        vals_idx += vals_size;
    }}

    return err;
    }}
    '''
    f.write(dedent(f_str))
    print("there are ", counter, "zero tiles")


if __name__ == '__main__':
    parse_gold(app_name, data)


