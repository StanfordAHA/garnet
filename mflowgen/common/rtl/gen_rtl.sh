#!/bin/bash
if [ $soc_only = True ]; then
  echo "soc_only set to true. Garnet not included"
  touch outputs/design.v
else
  flags="--width $array_width --height $array_height -v --no-sram-stub"
 
  if [ $PWR_AWARE == False ]; then
   flags+=" --no-pd"
  fi
 
  if [ $interconnect_only == True ]; then
   flags+=" --interconnect-only"
  fi
  
  if [ $use_container == True ]; then
    # Clone AHA repo
    git clone https://github.com/StanfordAHA/aha.git
    cd aha
    # install the aha wrapper script
    pip install -e .

    # pull docker image from docker hub
    docker pull stanfordaha/garnet:latest
    
    # run the container in the background and delete it when it exits
    # (this will print out the name of the container to attach to)
    container_name=$(aha docker)
    echo "container-name: $container_name"
    docker exec $container_name /bin/bash -c "source /aha/bin/activate && aha garnet $flags"
    docker cp $container_name:/aha/garnet/garnet.v ../outputs/design.v
    docker kill $container_name
    echo "killed docker container $container_name"
    cd ..
    
  else
    current_dir=$(pwd)
    cd $GARNET_HOME
    if [ -d "genesis_verif/" ]; then
      rm -rf genesis_verif
    fi
     
    eval "python garnet.py $flags"
    
    # If there are any genesis files, we need to cat those
    # with the magma generated garnet.v
    if [ -d "genesis_verif" ]; then
      cp garnet.v genesis_verif/garnet.sv
      cat genesis_verif/* >> $current_dir/outputs/design.v
    # Otherwise, garnet.v contains all rtl
    else
      cp garnet.v $current_dir/outputs/design.v
    fi
  fi 
  
  cd $current_dir
fi
