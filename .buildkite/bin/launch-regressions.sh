cat <<'EOF'
# ------------------------------------------------------------------------
- label: ":wrench: Aha regressions"
  agents: { hostname: $BUILDKITE_AGENT_META_DATA_HOSTNAME, docker: true }
  commands:

  # In case Lint step failed to clean up correctly
  - docker ps; docker kill $CONTAINER || true; sleep 10; docker ps

  # Container setup
  - docker run -id --name $CONTAINER --rm -v /cad:/cad $IMAGE bash
  - docker exec $CONTAINER /bin/bash -c "rm -rf /aha/garnet"
  - docker cp . $CONTAINER:/aha/garnet
  - docker cp /nobackup/zircon/MatrixUnit_sim_sram.v $CONTAINER:/aha/garnet/MatrixUnit_sim_sram.v
  - docker cp /nobackup/zircon/MatrixUnitWrapper_sim.v $CONTAINER:/aha/garnet/MatrixUnitWrapper_sim.v

  # Run the test(s)
  - docker exec $CONTAINER /bin/bash -c "
      source /aha/bin/activate;
      source /cad/modules/tcl/init/sh;
      module load base incisive xcelium/19.03.003 vcs/Q-2020.03-SP2;
      pwd; aha regress pr;
    "

EOF
