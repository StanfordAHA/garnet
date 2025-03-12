import sys

def main():
    f = open(sys.argv[1]) 

    print("\nPE MAX DELAYS")

    line = f.readline();

    while line:
        if 'Startpoint' in line:
            while 'Scenario' not in line:
                line = f.readline()
            scenario = line.split(":")[1].strip()
            while 'data arrival time' not in line:
                line = f.readline()
            time = line.split()[-1]
            print(f"{scenario}: {time} ns")

        line = f.readline()
    
    print()

if __name__ == '__main__':
    main()
