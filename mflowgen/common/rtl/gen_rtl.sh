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
    flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --no-sram-stub"

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

      # Prune docker images...
      yes | docker image prune -a --filter "until=6h" --filter=label='description=garnet' || true



##############################################################################
#which_container=cst
which_container=latest
if [ "$which_container" == "latest" ]; then

   # ORIGINAL CODE
      # pull docker image from docker hub
      docker pull stanfordaha/garnet:latest

      # run the container in the background and delete it when it exits
      # (this will print out the name of the container to attach to)
      container_name=$(aha docker)
      echo "container-name: $container_name"
else

   # TEMPORARY CST-CHECK HACK
      # pull docker image from docker hub
      docker pull stanfordaha/garnet:cst

      # run the container in the background and delete it when it exits
      # (this will print out the name of the container to attach to)
      container_name=cst
      echo "container-name: $container_name"
      # mount the /cad and name it, also run it as a daemon in background
      docker run -id --name ${container_name} --rm -v /cad:/cad stanfordaha/garnet:cst bash
fi
##############################################################################




      if [ $use_local_garnet == True ]; then
        docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
        # docker exec $container_name /bin/bash -c "cd /aha/lake/ && git checkout master && git pull"
        # Clone local garnet repo to prevent copying untracked files
        git clone $GARNET_HOME ./garnet
        docker cp ./garnet $container_name:/aha/garnet
      fi

      # run garnet.py in container and concat all verilog outputs
      docker exec $container_name /bin/bash -c \
        "
         # source /aha/bin/activate && aha garnet $flags;
         source /aha/bin/activate

         echo PIPCHECK BEGIN ----------------
         pip list -v |& egrep 'ast.t|peak|magma'
         echo ----------------
         echo ast_tools check; (cd /aha/ast_tools; git log | grep . | head -6); echo "---"
         echo magma     check; (cd /aha/magma;     git log | grep . | head -6); echo "---"
         echo peak      check; (cd /aha/peak;      git log | grep . | head -6); echo "---"
         echo PIPCHECK END --------------------

# alias piu='pip install -U --exists-action s -e'
# piu git://github.com/leonardt/ast_tools.git@cst#egg=ast_tools
# piu git://github.com/phanrahan/magma.git@cst#egg=magma-lang
# piu git://github.com/cdonovick/peak.git@cst#egg=peak

         aha garnet $flags;

         echo PIPCHECK BEGIN2 ----------------
         pip list -v |& egrep 'ast.t|peak|magma'
         echo ----------------
         echo ast_tools check; (cd /aha/ast_tools; git log | grep . | head -6); echo "---"
         echo magma     check; (cd /aha/magma;     git log | grep . | head -6); echo "---"
         echo peak      check; (cd /aha/peak;      git log | grep . | head -6); echo "---"
         echo PIPCHECK END2 --------------------

         cd garnet
         if [ -d "genesis_verif" ]; then
           cp garnet.v genesis_verif/garnet.v
           cat genesis_verif/* >> design.v
         else
           cp garnet.v design.v
         fi
         make -C global_buffer rtl CGRA_WIDTH=${array_width} NUM_GLB_TILES=$((array_width / 2))
         cat global_buffer/rtl/global_buffer_param.svh >> design.v
         cat global_buffer/rtl/global_buffer_pkg.svh >> design.v
         cat global_buffer/systemRDL/output/*.sv >> design.v
         cat global_buffer/rtl/*.sv >> design.v
         make -C global_controller rtl
         cat global_controller/systemRDL/output/*.sv >> design.v"
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

      # make to generate systemRDL RTL files global buffer
      make -C $GARNET_HOME/global_buffer rtl CGRA_WIDTH=${array_width}
      # Copy global buffer systemverilog from the global buffer folder
      cat global_buffer/rtl/global_buffer_param.svh >> $current_dir/outputs/design.v
      cat global_buffer/rtl/global_buffer_pkg.svh >> $current_dir/outputs/design.v
      cat global_buffer/systemRDL/output/*.sv >> $current_dir/outputs/design.v
      cat global_buffer/rtl/*.sv >> $current_dir/outputs/design.v
      # make to generate systemRDL RTL files for global controller
      make -C $GARNET_HOME/global_controller rtl CGRA_WIDTH=${array_width}
      cat global_controller/systemRDL/output/*.sv >> $current_dir/outputs/design.v
    fi

    cd $current_dir
  fi
fi

current_dir=$(pwd)
cd $START_DIR
  # cp outputs/design.v /tmp/design.v.$$
  # cp mflowgen-run.log /tmp/log.$$
  pwd; ls -l outputs/design.v mflowgen-run.log
  set -x
  cp outputs/design.v /tmp/design.v.${which_container}.deleteme$$
  cp mflowgen-run.log /tmp/cstlog.${which_container}.deleteme$$
  set +x
cd $current_dir
