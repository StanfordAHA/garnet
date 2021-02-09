def dump_reg_pair(f_reglist, f_regpair):
    with open(f_reglist, 'r') as reglist, open(f_regpair, 'w') as regpair:
        for line in reglist:
            if not line.startswith("0x"):
                continue
            word_list = line.split()
            addr = word_list[0]
            bits = word_list[6]
            data = 2**int(bits) - 1
            regpair.write(f"{addr},{data}\n")

if __name__ == "__main__":
    dump_reg_pair("systemRDL/output/glb.reglist", "glb.regpair")
