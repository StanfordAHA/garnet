#!/bin/bash

# Template for regression steps

template='
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
      aha regress pr;
    "
'

# Launch THREE regression steps, "regressions 123", 456, and 789.

for i in 1 4 7; do
    group=$i$((i+1))$((i+2))
    echo "$template" | sed "
      s/Aha regressions/Aha regressions $group/
      s/CONTAINER/CONTAINER-$group/g
      s/aha regress pr/aha regress pr_aha$((i++)); aha regress pr_aha$((i++)); aha regress pr_aha$((i++))/
    "
done
