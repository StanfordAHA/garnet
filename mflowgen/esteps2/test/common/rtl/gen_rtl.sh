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
    flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --no-sram-stub --glb_tile_mem_size $glb_tile_mem_size"

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
      # steveri 02/2021 - Original code only supported image "latest";
      # new code (below) allows use of any image based on new "which_image" parm

      # See common/rtl/configure.yml for "which_image" setting; default = "latest"
      if [ "$which_image" == "" ]; then which_image=latest; fi

      # Or can simply uncomment below to e.g. use image 'stanfordaha/garnet:cst'
      # which_image=cst

      # pull docker image from docker hub
      docker pull stanfordaha/garnet:${which_image}

      # Display ID info for image e.g.
      #     RepoTags    [stanfordaha/garnet:latest]
      #     RepoDigests [stanfordaha/garnet@sha256:e43c853b4068992...]
      docker inspect --format='RepoTags    {{.RepoTags}}'    stanfordaha/garnet:${which_image}
      docker inspect --format='RepoDigests {{.RepoDigests}}' stanfordaha/garnet:${which_image}

      if [ "$which_image" == "latest" ]; then
          # run the container in the background and delete it when it exits
          # ("aha docker" will print out the name of the container to attach to)
          container_name=$(aha docker)
      else
          # run the container in the background and delete it when it exits (--rm)
          # mount /cad and name it, and run container as a daemon in background
          container_name=${which_image}
          docker run -id --name ${container_name} --rm -v /cad:/cad stanfordaha/garnet:cst bash
      fi
      echo "container-name: $container_name"
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
        '# Func to check python package creds (Added 02/2021 as part of cst vetting)
         # (Single-quote regime)

         function checkpip {
             # Example: checkpip ast.t "peak "
             #   ast-tools           0.0.30    /aha/ast_tools
             #   6b779e    Merge pull request #70 from leonardt/arg-fix
             #   ---
             #   peak                0.0.1     /aha/peak
             #   fa4635    Move to libcst
             for p in "$@"; do
                 if ! pip list -v |& egrep "$p";
                 then echo "Cannot find package \"$p\""; continue; fi
                 src_dir=$(pip list -v |& grep $p | awk "{print \$NF}")
                 echo -n $(cd $src_dir; git log | head -1 | awk "{print substr(\$2,1,6)}" )
                 (cd $src_dir; git log | egrep "^ " | head -1)
                 echo "---"
             done
         }'"
         # (Double-quote regime)
         source /aha/bin/activate; # Set up the build environment

         # Example: say you want to double-check packages 'ast_tools', 'magma', and 'peak'.
         # Uncomment the line below; This will display the version,
         # location and latest commit hash for each.
         # echo '+++ PIPCHECK-BEFORE'; checkpip ast.t magma 'peak '; echo '--- Continue build'

         aha garnet $flags; # Here is where we build the verilog for the main chip

         # Rename output verilog, final name must be 'design.v'
         cd garnet
         if [ -d 'genesis_verif' ]; then
           cp garnet.v genesis_verif/garnet.v
           cat genesis_verif/* >> design.v
         else
           cp garnet.v design.v
         fi
         make -C global_buffer rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
         cat global_buffer/rtl/global_buffer_param.svh >> design.v
         cat global_buffer/rtl/global_buffer_pkg.svh >> design.v
         cat global_buffer/systemRDL/output/*.sv >> design.v
         cat global_buffer/rtl/gl*.sv >> design.v
         make -C global_controller rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
         cat global_controller/systemRDL/output/*.sv >> design.v"

      # Copy the concatenated design.v output out of the container
      docker cp $container_name:/aha/garnet/design.v ../outputs/design.v
      # Kill the container
      docker kill $container_name
      echo "killed docker container $container_name"
      cd .. ; # pop out from e.g. "9-rtl/aha/" back to "9-rtl/"

      # Set 'save_verilog_to_tmpdir' "True" if want to capture the output
      # design from buildkite, e.g. to compare before-and-after versions of
      # docker images "latest" and "new" (also see notes in configure.yml)

      if [ "$save_verilog_to_tmpdir" == "True" ]; then
          echo "+++ ENDGAME - Save verilog to /tmp before buildkite deletes it"
          set -x; # so user will know where the files are going
          cp outputs/design.v /tmp/design.v.${which_image}.deleteme$$
          cp mflowgen-run.log /tmp/log.${which_image}.deleteme$$
          set +x
      fi

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
      make -C $GARNET_HOME/global_buffer rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
      # Copy global buffer systemverilog from the global buffer folder
      cat global_buffer/rtl/global_buffer_param.svh >> $current_dir/outputs/design.v
      cat global_buffer/rtl/global_buffer_pkg.svh >> $current_dir/outputs/design.v
      cat global_buffer/systemRDL/output/*.sv >> $current_dir/outputs/design.v
      cat global_buffer/rtl/gl*.sv >> $current_dir/outputs/design.v
      # make to generate systemRDL RTL files for global controller
      make -C $GARNET_HOME/global_controller rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
      cat global_controller/systemRDL/output/*.sv >> $current_dir/outputs/design.v

      cd $current_dir ; # why? all we do after this is exit back to calling dir...?
    fi
  fi
fi

