import random

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

def gen_data_sample(filename, num):
    with open(filename, 'w') as f:
        f.write(f"{num}\n")
        for i in range(num):
            x = random.randrange(0, 2**16)
            f.write(f"{x} ")

if __name__ == "__main__":
    gen_reg_pair("systemRDL/output/glb.reglist", "glb.regpair")
    gen_data_sample("glb.test.data16", 32)
    gen_bs_sample("glb.test.bs", 32)
