#!/bin/bash

# Build up the flags we want to pass to python garnet.v
flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --interconnect-only"
map_flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval --interconnect-only"

if [ ${PWR_AWARE} = "False" ]; then
  flags="$flags --no-pd"
  map_flags="$map_flags --no-pd"
fi

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

# docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
# # Clone local garnet repo to prevent copying untracked files
# git clone $GARNET_HOME ./garnet
# docker cp ./garnet $container_name:/aha/garnet
# run the tests in the container and get all relevant files (tb, place file)
docker exec $container_name /bin/bash -c \
  "source /cad/modules/tcl/init/bash;
   module load xcelium;
   source /aha/bin/activate;
   aha garnet ${flags};
   cd garnet;"

for app in $(echo $cgra_apps | sed "s/,/ /g")
do
    set -xe;
    docker exec $container_name /bin/bash -c \
      "source /aha/bin/activate;
       aha halide ${app};
       aha map ${app} ${map_flags};
       mkdir -pv /aha/meta/${app}/bin
       cp /aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}/bin/design.meta /aha/meta/${app}/bin/design.meta;
       cp /aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}/bin/design.place /aha/meta/${app}/bin/design.place;
       cp /aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}/bin/*.bs /aha/meta/${app}/bin/;
       cp /aha/Halide-to-Hardware/apps/hardware_benchmarks/${app}/bin/*.raw /aha/meta/${app}/bin/;"
done

docker cp $container_name:/aha/meta ../outputs

# # Kill the container
docker kill $container_name
echo "killed docker container $container_name"
cd $current_dir
