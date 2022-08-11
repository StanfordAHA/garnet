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


def gen_data_sample(filename, width, num_data, num_blocks):
    with open(filename, 'w') as f:
        # f.write(f"{num}\n")
        if num_blocks == 0:
            for i in range(num_data):
                x = random.randrange(0, 2**width)
                f.write(f"{hex(x)[2:]} ")
        else:
            for i in range(num_blocks):
                if i == num_blocks - 1:
                    block_size = num_data // num_blocks + num_data % num_blocks
                else:
                    block_size = num_data // num_blocks

                f.write(f"{hex(block_size)[2:]} ")
                for j in range(block_size):
                    x = random.randrange(0, 2**width)
                    f.write(f"{hex(x)[2:]} ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='testvector generator')
    parser.add_argument('--data', type=str, default=None)
    parser.add_argument('--width', type=int, default=16)
    parser.add_argument('--num_data', type=int, default=32)
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--num_blocks', type=int, default=0)
    parser.add_argument('--bitstream', type=str, default=None)
    parser.add_argument('--bitstream-size', type=int, default=32)
    args = parser.parse_args()
    random.seed(args.seed)
    if args.config:
        gen_reg_pair("../systemRDL/output/glb.reglist", args.config)
    if args.bitstream:
        gen_bs_sample(args.bitstream, args.bitstream_size)
    if args.data:
        gen_data_sample(args.data, args.width, args.num_data, args.num_blocks)
