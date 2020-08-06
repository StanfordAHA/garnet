#!/bin/bash
# Hierarchical flows can accept RTL as an input from parent graph
if [ -f ../inputs/design.v ]; then
  echo "Using RTL from parent graph"
  mkdir -p outputs
  (cd outputs; ln -s ../../inputs/design.v)
else
  if [ $soc_only = True ]; then
    echo "soc_only set to true. Garnet not included"
    touch outputs/design.v
  else
    # Clean out old rtl outputs
    rm -rf $GARNET_HOME/genesis_verif
    rm -f $GARNET_HOME/garnet.v
  
    # Build up the flags we want to pass to python garnet.v
    flags="--width $array_width --height $array_height -v --no-sram-stub"
   
    if [ $PWR_AWARE == False ]; then
     flags+=" --no-pd"
    fi
   
    if [ $interconnect_only == True ]; then
     flags+=" --interconnect-only"
    fi
   
    # Use aha docker container for all dependencies 
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
  
      if [ $use_local_garnet == True ]; then
        docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
        # Clone local garnet repo to prevent copying untracked files
        git clone $GARNET_HOME ./garnet
        docker cp ./garnet $container_name:/aha/garnet
      fi
  
      # run garnet.py in container and concat all verilog outputs
      docker exec $container_name /bin/bash -c \
        "source /aha/bin/activate && aha garnet $flags;
         cd garnet
         if [ -d "genesis_verif" ]; then
           cp garnet.v genesis_verif/garnet.v
           cat genesis_verif/* >> design.v
         else
           cp garnet.v design.v
         fi"
      # Copy the concatenated design.v output out of the container
      docker cp $container_name:/aha/garnet/design.v ../outputs/design.v
      # Kill the container
      docker kill $container_name
      echo "killed docker container $container_name"
      cd ..
    
    # Else we want to use local python env to generate rtl 
    else
      current_dir=$(pwd)
      cd $GARNET_HOME
       
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
fi
