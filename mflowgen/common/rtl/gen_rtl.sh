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
  echo '--- gen_rtl END' `date +%H:%M`
  exit
fi

# Did not find existing design.v. Generate a new one UNLESS soc_only is true
if [ $soc_only = True ]; then
    echo "soc_only set to true. Garnet not included"
    touch outputs/design.v
    echo '--- gen_rtl END' `date +%H:%M`
    exit
fi

##############################################################################
# Generate design.v

# Clean out old rtl outputs
rm -rf $GARNET_HOME/genesis_verif
rm -f  $GARNET_HOME/garnet.v

# Build up the flags we want to pass to python garnet.v
flags="--width $array_width --height $array_height"
flags+=" --pipeline_config_interval $pipeline_config_interval"
flags+=" -v --glb_tile_mem_size $glb_tile_mem_size"

# sparsity flags for onyx
[ "$WHICH_SOC" != "amber" ] && flags+=" --rv --sparse-cgra --sparse-cgra-combined"

# Default is power-aware, but can be turned off
[ $PWR_AWARE == False ] && flags+=" --no-pd"

# Where/when is this used?
[ $interconnect_only == True ] && flags+=" --interconnect-only"

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

#       if [ "$WHICH_SOC" == "amber" ]; then
#           # NOW: to make this branch (master-tsmc) work, must use specific docker image
#           # FIXME/TODO: should be part of top-level parms
#           # FIXME/TODO: whrere are top-level parms???
#           amber_dense_sha=dd688c7b98b034dadea9f7177781c97a7a030d737ae4751a78dbb97ae8b72af4
#           default_image="stanfordaha/garnet@sha256:${amber_dense_sha}"
#       fi

      if [ "$rtl_docker_image" == ""        ]; then rtl_docker_image=${default_image}; fi
      if [ "$rtl_docker_image" == "default" ]; then rtl_docker_image=${default_image}; fi

# No longer available maybe; it just causes trouble maybe
#       
#       # Env var overrides all else
#       if [ "$RTL_DOCKER_IMAGE" ]; then
#           echo "+++ WARNING overriding local rtl_docker_image w env var RTL_DOCKER_IMAGE"
#           echo "WAS $rtl_docker_image"
#           rtl_docker_image=${RTL_DOCKER_IMAGE}
#           echo "NOW $rtl_docker_image"
#           echo "--- continue..."
#       fi

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
        # Clone local garnet repo to prevent copying untracked files
        git clone $GARNET_HOME ./garnet
        docker cp ./garnet $container_name:/aha/garnet
      fi
      
      # N'EXISTE PAS
      # archipelago          ec505e6     80 (a1,b79)        kuree/archipelago


      # How does amber config differ from onyx default?
      # (Optimally this would be the empty set :( )
      amber_diffs='
            Halide-to-Hardware   e8798fa     84 (a2,b82)        stanfordaha/Halide-to-Hardware
            MetaMapper           e25b6f6      1 (a0,b1)         rdaly525/MetaMapper
            archipelago          f35e6e5
            canal                6fec524     19 (a19,b0)        stanfordaha/canal
            clockwork            efdd95e    135 (a0,b135)       dillonhuff/clockwork
            gemstone             28b10a6      9 (a9,b0)         stanfordaha/gemstone
            kratos               873b369     91 (a91,b0)        kuree/kratos
            lake                 837ffe1      2 (a2,b0)         StanfordAHA/lake
            lassen               70edcf3      2 (a2,b0)         stanfordaha/lassen
            mantle               fb8532a      2 (a2,b0)         phanrahan/mantle
            peak                 9a24cf7     10 (a10,b0)        cdonovick/peak
            pycoreir             80e072e     30 (a30,b0)        leonardt/pycoreir
       '

      # Update container for amber config if necessary
      if [ "$WHICH_SOC" == "amber" ]; then
          echo "+++ Updating container with amber diffs"
          echo "$amber_diffs"
          echo "------------------------------------------------------------------------"

          echo "BEFORE:"
          docker exec $container_name /bin/bash -c "git submodule status"
          echo "------------------------------------------------------------------------"

          # E.g. updates="cd /aha/garnet   && git checkout 9982932
          #               cd /aha/gemstone && git checkout 28b10a6
          #               cd /aha/kratos   && git checkout 873b369
          #               cd /aha/lake     && git checkout 837ffe1"

          updates=`echo "$amber_diffs" | awk 'NF>=2{printf( "cd /aha/%-18s && git checkout %s\n", $1, $2 )}'`
          echo "$updates"
          echo "------------------------------------------------------------------------"

          echo "$updates" | while read u; do 
              echo "docker exec $container_name /bin/bash -c '$u'"
              docker exec $container_name /bin/bash -c "$u"
              printf "\n"
          done
          echo "------------------------------------------------------------------------"
          echo "AFTER:"
          docker exec $container_name /bin/bash -c "git submodule status"
          echo "------------------------------------------------------------------------"
          echo "--- continue..."
      fi
      
      #docker exec $container_name /bin/bash -c "cd /aha && git checkout master && git pull && git submodule update"
      #docker exec $container_name /bin/bash -c "cd /aha/lake/ && git fetch origin && git checkout sparse_strawman && git pull"
      #docker exec $container_name /bin/bash -c "cd /aha/kratos/ && git checkout master && git pull && DEBUG=1 pip install -e ."

      # run garnet.py in container and concat all verilog outputs
      echo "---docker exec $container_name"

      docker exec $container_name /bin/bash -c \
        '# Func to check python package creds (Added 02/2021 as part of cst vetting)
         # (Single-quote regime)

         # Oh what a hack
         export WHICH_SOC='$WHICH_SOC'

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
else    # if NOT [ $use_container == True ]
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


echo '--- gen_rtl END' `date +%H:%M`
