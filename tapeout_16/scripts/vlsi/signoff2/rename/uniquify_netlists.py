#! /usr/bin/python


import sys
import fileinput

words = sys.argv[1:]  # note that split without arguments splits on whitespace
pairs = [words[i*2]+' '+words[i*2+1] for i in range(len(words)/2)]

counter = 1
for x in pairs:
    subckts = []
    (filename, cell) = x.split()

    for line in fileinput.input(filename, inplace=True, backup='.bak'):
        if '.subckt' in line.lower():
            s = line.strip().split()
            name = s[1]
            # [stevo]: ndio_mac is in memories, causes LVS issues when
            # uniquified
            if name != cell and name != "ndio_mac":
                subckts.append(name)
                if cell == "CLK_RX_amp_buf":
                    name = name + '_WB%d' % (counter)
                else:
                    name = name + '_uniq%d' % (counter)
                s[1] = name
            line = ' '.join(s) + '\n'
        print(line)

    for line in fileinput.input(filename, inplace=True, backup='.bak'):
        for subckt in subckts:
            s = line.strip().split()
            if subckt in s:
                for i, j in enumerate(s):
                    if j == subckt:
                        if cell == "CLK_RX_amp_buf":
                            s[i] = subckt + '_WB%d' % (counter)
                        else:
                            s[i] = subckt + '_uniq%d' % (counter)
                line = ' '.join(s) + '\n'
        print(line)

    counter = counter + 1
