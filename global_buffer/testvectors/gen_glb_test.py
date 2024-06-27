import random
import argparse


def gen_reg_pair(f_reglist, f_regpair):
    with open(f_reglist, 'r') as reglist:
        num = 0
        for line in reglist:
            if line.startswith("0x"):
                num += 1

    with open(f_reglist, 'r') as reglist, open(f_regpair, 'w') as regpair:
        regpair.write(f"{num}\n")
        for line in reglist:
            if not line.startswith("0x"):
                continue
            word_list = line.split()
            addr = word_list[0][2:]
            bits = word_list[6]
            data = 2**int(bits) - 1
            regpair.write(f"{addr} {data}\n")


def gen_bs_sample(filename, num):
    with open(filename, 'w') as f:
        f.write(f"{num}\n")
        for i in range(num):
            # addr = random.randrange(0, 2**32)
            col = random.randrange(0, 32)
            reg = random.randrange(0, 2**8)
            data = random.randrange(0, 2**32)
            f.write(f"{(reg << 8 ) | col} ")
            f.write(f"{data}\n")


def gen_data_sample(filename, width, num_data, num_blocks, seg_mode):
    with open(filename, 'w') as f:
        # f.write(f"{num}\n")
        if num_blocks == 0:
            for i in range(num_data):
                x = random.randrange(0, 2**width)
                f.write(f"{hex(x)[2:]} ")
        else:
            max_block_size = num_data // num_blocks + num_data % num_blocks
            if seg_mode == 0:
                stride = (max_block_size + 1) * 2 + 8
            else:
                stride = (max_block_size + 2) * 2 + 8
            stride -= stride % 8  # always use a new word line
            addr_list = [i * stride for i in range(num_blocks)]
            input_list = [[] for i in range(num_blocks)]

            gold_file = filename.replace(".dat", ".gold")
            with open(gold_file, 'w') as gold_f:
                for i in range(num_blocks):
                    if i == num_blocks - 1:
                        block_size = num_data // num_blocks + num_data % num_blocks
                    else:
                        block_size = num_data // num_blocks
                    
                    if seg_mode == 0:
                        input_list[i].append(addr_list[i])
                        input_list[i].append(block_size)
                        gold_f.write(f"{hex(block_size)[2:]} ")
                        for j in range(block_size):
                            x = random.randrange(0, 2**width)
                            input_list[i].append(i+1)
                            gold_f.write(f"{hex(i+1)[2:]} ")
                        for j in range(stride//2 - block_size - 1):
                            gold_f.write(f"{hex(0)[2:]} ")
                    else:
                        seg_size = random.randrange(1, block_size)
                        crd_size = block_size - seg_size

                        input_list[i].append(addr_list[i])
                        input_list[i].append(seg_size)
                        gold_f.write(f"{hex(seg_size)[2:]} ")
                        for j in range(seg_size):
                            x = random.randrange(0, 2**width)
                            input_list[i].append(i+1)
                            gold_f.write(f"{hex(i+1)[2:]} ")
                        
                        input_list[i].append(crd_size)
                        gold_f.write(f"{hex(crd_size)[2:]} ")
                        for j in range(crd_size):
                            x = random.randrange(0, 2**width)
                            input_list[i].append(i+17)
                            gold_f.write(f"{hex(i+17)[2:]} ")
                        for j in range(stride//2 - block_size - 2):
                            gold_f.write(f"{hex(4095)[2:]} ")  # padding

            random.shuffle(input_list)
            for i in range(num_blocks):
                for j in range(len(input_list[i])):
                    f.write(f"{hex(input_list[i][j])[2:]} ")

            # gold_file = filename.replace(".dat", ".gold")
            # with open(gold_file, 'w') as gold_f:
            #     for i in range(num_blocks):
            #         if i == num_blocks - 1:
            #             block_size = num_data // num_blocks + num_data % num_blocks
            #         else:
            #             block_size = num_data // num_blocks

            #         f.write(f"{hex(addr_list[i])[2:]} ")
            #         f.write(f"{hex(block_size)[2:]} ")
            #         gold_f.write(f"{hex(block_size)[2:]} ")
            #         for j in range(block_size):
            #             x = random.randrange(0, 2**width)
            #             f.write(f"{hex(1)[2:]} ")
            #             gold_f.write(f"{hex(1)[2:]} ")
            #             # f.write(f"{hex(x)[2:]} ")
            #             # gold_f.write(f"{hex(x)[2:]} ")
            #         for j in range(stride - block_size - 1):
            #             gold_f.write(f"{hex(0)[2:]} ")

                # for i in range(num_blocks):
                #     if i == num_blocks - 1:
                #         block_size = num_data // num_blocks + num_data % num_blocks
                #     else:
                #         block_size = num_data // num_blocks

                #     f.write(f"{hex(block_size)[2:]} ")
                #     for j in range(block_size):
                #         x = random.randrange(0, 2**width)
                #         f.write(f"{hex(x)[2:]} ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='testvector generator')
    parser.add_argument('--data', type=str, default=None)
    parser.add_argument('--width', type=int, default=16)
    parser.add_argument('--num_data', type=int, default=32)
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--num_blocks', type=int, default=0)
    parser.add_argument('--seg_mode', type=int, default=0)
    parser.add_argument('--bitstream', type=str, default=None)
    parser.add_argument('--bitstream-size', type=int, default=32)
    args = parser.parse_args()
    random.seed(args.seed)
    if args.config:
        gen_reg_pair("../systemRDL/output/glb.reglist", args.config)
    if args.bitstream:
        gen_bs_sample(args.bitstream, args.bitstream_size)
    if args.data:
        gen_data_sample(args.data, args.width, args.num_data, args.num_blocks, args.seg_mode)
