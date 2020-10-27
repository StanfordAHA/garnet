#!/bin/bash

# Build up the flags we want to pass to python garnet.v
flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --no-sram-stub --no-pd --interconnect-only"

map_flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval --no-pd --interconnect-only"

# Clone AHA repo
git clone https://github.com/StanfordAHA/aha.git
cd aha
# install the aha wrapper script
pip install -e .

# Prune docker images...
yes | docker image prune -a --filter "until=6h" --filter=label='description=garnet' || true
docker container prune -f
# pull docker image from docker hub
docker pull stanfordaha/garnet:latest

# run the container in the background and delete it when it exits
# (this will print out the name of the container to attach to)
container_name=$(aha docker)
echo "container-name: $container_name"

docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
# Clone local garnet repo to prevent copying untracked files
git clone $GARNET_HOME ./garnet
docker cp ./garnet $container_name:/aha/garnet
# run the tests in the container and get all relevant files (tb, place file)
docker exec $container_name /bin/bash -c \
  "source /cad/modules/tcl/init/bash;
   module load incisive;
   source /aha/bin/activate;
   aha garnet ${flags};
   cd garnet;
   sed -i 's|tester.expect(self.circuit.read_config_data, value)|# removed expect|' tbg.py;
   aha halide ${app_to_run};
   aha map ${app_to_run} ${map_flags};
   aha test ${app_to_run};"
# Copy the testbench, input file, and placement file out of the container
docker cp $container_name:/aha/garnet/temp/garnet/Interconnect_tb.sv ../outputs/testbench.sv
# Fix testbench file paths
sed -i "s|/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app_to_run}/bin/|./inputs/|g" ../outputs/testbench.sv
docker cp $container_name:/aha/garnet/temp/design.place ../outputs/design.place
docker cp $container_name:/aha/Halide-to-Hardware/apps/hardware_benchmarks/${app_to_run}/bin/input.raw ../outputs/input.raw
# Kill the container
#docker kill $container_name
echo "killed docker container $container_name"
cd $current_dir
