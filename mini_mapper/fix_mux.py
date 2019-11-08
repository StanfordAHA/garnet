from __future__ import print_function
import json


def fix_mux_order(input_filename, output_filename):
    with open(input_filename) as f:
        data = json.load(f)
        f.seek(0, 0)
        raw_lines = f.readlines()
    connections = \
        data["namespaces"]["global"]["modules"]["DesignTop"]["connections"]
    instances = data["namespaces"]["global"]["modules"]["DesignTop"][
        "instances"]
    # first pass to find all the mux instances
    mux_set = find_mux(instances)
    print("We have", len(mux_set), "muxes to fix:")
    for mux in mux_set:
        print(mux)

    connection_to_add = []
    connection_to_remove = []
    total_muxes_len = len(mux_set)
    total_muxes = mux_set.copy()

    while len(mux_set) > 0:
        mux_name = mux_set.pop()

        for conn1, conn2 in connections:
            conn1_name = conn1.split(".")[0]
            conn2_name = conn2.split(".")[0]
            if conn1_name == mux_name:
                if conn1[-1] == "0" and "bit" not in conn1:
                    connection_to_remove.append([conn1, conn2])
                    new_conn1 = conn1[:-1] + "1"
                    connection_to_add.append((new_conn1, conn2))
                elif conn1[-1] == "1" and "bit" not in conn1:
                    connection_to_remove.append([conn1, conn2])
                    new_conn1 = conn1[:-1] + "0"
                    connection_to_add.append((new_conn1, conn2))
            elif conn2_name == mux_name:
                if conn2[-1] == "0" and "bit" not in conn2:
                    connection_to_remove.append([conn1, conn2])
                    new_conn2 = conn2[:-1] + "1"
                    connection_to_add.append((conn1, new_conn2))
                elif conn2[-1] == "1" and "bit" not in conn2:
                    connection_to_remove.append([conn1, conn2])
                    new_conn2 = conn2[:-1] + "0"
                    connection_to_add.append((conn1, new_conn2))

    assert (len(connection_to_remove) == len(connection_to_add))
    assert (len(connection_to_remove) == total_muxes_len * 2)

    # save to output
    count = 0
    with open(output_filename, "w+") as f:
        for i in range(len(raw_lines)):
            line = raw_lines[i]
            for j in range(len(connection_to_remove)):
                conn1, conn2 = connection_to_remove[j]
                if conn1 in line and conn2 in line:
                    new_conn1, new_conn2 = connection_to_add[j]
                    line = line.replace(conn1, new_conn1)
                    line = line.replace(conn2, new_conn2)
                    count += 1
                    break
            f.write(line)
        print("result saved to", output_filename)
    assert count == len(connection_to_remove)


def find_mux(instances):
    mux_set = set()
    for instance_name in instances:
        instance = instances[instance_name]
        if "modargs" in instance:
            if "alu_op" in instance["modargs"] and \
                    instance["modargs"]["alu_op"][-1] == "sel":
                # if "enMux" not in instance_name:
                #    mux_set.add(instance_name)
                mux_set.add(instance_name)
    return mux_set
