#!/bin/bash
set -e; # DIE if any of the below commands exits with error status

echo '--- gen_rtl BEGIN' `date +%H:%M`

# Hierarchical flows can accept RTL as an input from parent graph
if [ -f ../inputs/design.v ]; then
  echo "Using RTL from parent graph"
  mkdir -p outputs
  (cd outputs; ln -s ../../inputs/design.v)
  if [ -d ../inputs/header ]; then
    echo "Using header from parent graph"
    (cd outputs; ln -s ../../inputs/header)
  fi
else
  if [ $soc_only = True ]; then
    echo "soc_only set to true. Garnet not included"
    touch outputs/design.v
  else
    # Clean out old rtl outputs
    rm -rf $GARNET_HOME/genesis_verif
    rm -f $GARNET_HOME/garnet.v

    # Build up the flags we want to pass to python garnet.v
    flags="--width $array_width --height $array_height --pipeline_config_interval $pipeline_config_interval -v --glb_tile_mem_size $glb_tile_mem_size"

    if [ $PWR_AWARE == False ]; then
     flags+=" --no-pd"
    fi

    if [ $interconnect_only == True ]; then
     flags+=" --interconnect-only"
    fi

    # Use aha docker container for all dependencies
    if [ $use_container == True ]; then
      echo "Use aha docker container for all dependencies"

      # Clone AHA repo
      echo '--- gen_rtl aha clone BEGIN' `date +%H:%M`
      git clone https://github.com/StanfordAHA/aha.git
      cd aha

      # Prune docker images...
      # ("yes" emits endless stream of y's)
      echo '--- gen_rtl docker prune BEGIN' `date +%H:%M`
      yes | docker image prune -a --filter "until=6h" --filter=label='description=garnet' || true

      echo ""; echo "After pruning:"; echo ""
      docker images; echo ""
      docker ps    ; echo ""

      # Choose a docker image; can set via "rtl_docker_image" parameter
      default_image="stanfordaha/garnet:latest"
      if [ "$rtl_docker_image" == ""        ]; then rtl_docker_image=${default_image}; fi
      if [ "$rtl_docker_image" == "default" ]; then rtl_docker_image=${default_image}; fi

      # To use a docker image with name other than "latest" can do e.g.
      # rtl_docker_image="stanfordaha/garnet:cst"

      # To use a docker image based on sha hash can do e.g.
      # rtl_docker_image="stanfordaha/garnet@sha256:1e4a0bf29f3bad8e3..."

      echo '--- gen_rtl docker pull BEGIN' `date +%H:%M`
      echo "Using image '$rtl_docker_image'"
      docker pull ${rtl_docker_image}

      # Display ID info for image e.g.
      #     RepoTags    [stanfordaha/garnet:latest]
      #     RepoDigests [stanfordaha/garnet@sha256:e43c853b4068992...]
      docker inspect --format='RepoTags    {{.RepoTags}}'    ${rtl_docker_image}
      docker inspect --format='RepoDigests {{.RepoDigests}}' ${rtl_docker_image}

      # Run (container in the background and delete it when it exits (--rm)
      # Mount /cad and name it, and run container as a daemon in background
      # Use container_name "gen_rtl_<proc_id>"

      echo "Using docker container '$container_name'"
      container_name=gen_rtl_$$
      docker run -id --name ${container_name} --rm -v /cad:/cad ${rtl_docker_image} bash

      # MAKE SURE the docker container gets killed when this script dies.
      trap "docker kill $container_name" EXIT

      if [ $use_local_garnet == True ]; then
        docker exec $container_name /bin/bash -c "rm -rf /aha/garnet"
        # docker exec $container_name /bin/bash -c "cd /aha/lake/ && git checkout master && git pull"
        # Clone local garnet repo to prevent copying untracked files
        git clone $GARNET_HOME ./garnet
        docker cp ./garnet $container_name:/aha/garnet
      fi

      # run garnet.py in container and concat all verilog outputs
      echo "---docker exec $container_name"

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
         set -e; # DIE if any single command exits with error status
         # (Double-quote regime)
         # Example: say you want to double-check packages 'ast_tools', 'magma', and 'peak'.
         # Uncomment the line below; This will display the version,
         # location and latest commit hash for each.
         # echo '+++ PIPCHECK-BEFORE'; checkpip ast.t magma 'peak '; echo '--- Continue build'

         source /aha/bin/activate; # Set up the build environment

         if [ $interconnect_only == True ]; then
           echo --- INTERCONNECT_ONLY: aha garnet $flags
           aha garnet $flags; # Here is where we build the verilog for the main chip
           cd garnet
           cp garnet.v design.v
         elif [ $glb_only == True ]; then
           cd garnet

           echo '--- GLB_ONLY requested; do special glb things'
           echo make -C global_buffer rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
           make -C global_buffer rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
           cp global_buffer/global_buffer.sv design.v
           cat global_buffer/systemRDL/output/glb_pio.sv >> design.v
           cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> design.v
           cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> design.v
         else
           echo --- DEFAULT rtl build: aha garnet $flags
           # Rename output verilog, final name must be 'design.v'
           aha garnet $flags; # Here is where we build the verilog for the main chip
           cd garnet
           if [ -d 'genesis_verif' ]; then
             cp garnet.v genesis_verif/garnet.v
             cat genesis_verif/* >> design.v
           else
             cp garnet.v design.v
           fi
           cat global_buffer/systemRDL/output/glb_pio.sv >> design.v
           cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> design.v
           cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> design.v
           cat global_controller/systemRDL/output/*.sv >> design.v
         fi"


      echo '--- gen_rtl docker cleanup BEGIN' `date +%H:%M`

      # Copy the concatenated design.v output out of the container
      docker cp $container_name:/aha/garnet/design.v ../outputs/design.v
      if [ $glb_only == True ]; then
        docker cp $container_name:/aha/garnet/global_buffer/header ../outputs/header
      elif [ $interconnect_only == False ]; then
        docker cp $container_name:/aha/garnet/global_buffer/header ../glb_header
        docker cp $container_name:/aha/garnet/global_controller/header ../glc_header
        mkdir ../outputs/header
        cp -r ../glb_header/* ../outputs/header/
        cp -r ../glc_header/* ../outputs/header/
      fi

      # See whassup with docker atm
      docker ps
      docker images --digests

      # Kill the container
      if docker kill $container_name; then
          echo "killed docker container $container_name"
      else
          echo "could not kill docker container $container_name (maybe already dead?)"
      fi
      trap - EXIT; # Remove the docker-kill trap, don't need it anymore.

      cd .. ; # pop out from e.g. "9-rtl/aha/" back to "9-rtl/"

      # Set 'save_verilog_to_tmpdir' "True" if want to capture the output
      # design from buildkite, e.g. to compare before-and-after versions of
      # docker images "latest" and "new" (also see notes in configure.yml)

      if [ "$save_verilog_to_tmpdir" == "True" ]; then
          echo "+++ ENDGAME - Save verilog to /tmp before buildkite deletes it"
          set -x; # so user will know where the files are going
          cp outputs/design.v /tmp/design.v.${container_name}.deleteme$$
          cp mflowgen-run.log /tmp/log.${container_name}.deleteme$$
          set +x
      fi
      set +x

    # Else we want to use local python env to generate rtl
    else
      current_dir=$(pwd)
      cd $GARNET_HOME

      if [ $interconnect_only == True ]; then
        eval "python garnet.py $flags"
        cp garnet.v $current_dir/outputs/design.v
      elif [ $glb_only == True ]; then
        make -C global_buffer rtl CGRA_WIDTH=${array_width} GLB_TILE_MEM_SIZE=${glb_tile_mem_size}
        cp global_buffer/global_buffer.sv $current_dir/outputs/design.v
        cat global_buffer/systemRDL/output/glb_pio.sv >> $current_dir/outputs/design.v
        cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> $current_dir/outputs/design.v
        cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> $current_dir/outputs/design.v
      else
        eval "python garnet.py $flags"
        cp garnet.v $current_dir/outputs/design.v
        if [ -d 'genesis_verif' ]; then
          cp garnet.v genesis_verif/garnet.v
          cat genesis_verif/* >> $current_dir/outputs/design.v
        else
          cp garnet.v $current_dir/outputs/design.v
        fi
        cat global_buffer/systemRDL/output/glb_pio.sv >> $current_dir/outputs/design.v
        cat global_buffer/systemRDL/output/glb_jrdl_decode.sv >> $current_dir/outputs/design.v
        cat global_buffer/systemRDL/output/glb_jrdl_logic.sv >> $current_dir/outputs/design.v
        cat global_controller/systemRDL/output/*.sv >> $current_dir/outputs/design.v
      fi
      if [ $glb_only == True ]; then
        cp -r global_buffer/header $current_dir/outputs/header
      elif [ $interconnect_only == False ]; then
        cp -r global_buffer/header $current_dir/outputs/header
        cp -r global_controller/header/* $current_dir/outputs/header/
      fi
      cd $current_dir ;
    fi
  fi
fi

echo '--- gen_rtl END' `date +%H:%M`
