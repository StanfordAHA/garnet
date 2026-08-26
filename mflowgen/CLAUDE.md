# CLAUDE.md — garnet/mflowgen session notes

Notes for Claude sessions working on the **lake-spec MemCore PnR sweep**:
pushing per-spec memory-tile (`Tile_MemCore`) RTL through the mflowgen
physical-design flow (synth → place → CTS → route → signoff) for a range of
memory specifications, without changing the default (non-spec) onyx MemCore.

Read `/aha/lake/CLAUDE.md` §5 for the *lake-side* RTL-generation details
(tech-map/column selection, dual-port fixes). This file covers the *garnet
+ mflowgen* side.

## The sweep driver: `sweep_specs.py`

`./mflowgen/sweep_specs.py` builds one independent mflowgen workspace per
spec point. A spec point is a dict (`storage_capacity, data_width, vec_width,
in_ports, out_ports, dual_port`) in `DEFAULT_SPEC_POINTS`; its `_config_name`
is e.g. `fw2_dw16_sc4096_dp_in2_out2_vc2`.

Per config it writes `spec_config.json` into the workspace, runs `mflowgen
run` against `--graph` (default `mflowgen/Tile_MemCore`), then makes the
target chain up to `--stop-after` (default `cadence-innovus-signoff`).
Results (pass/fail, macro, workspace) go to `<out-dir>/results.csv`.

Key flags:
- `--preset {smoke4,full}` — named subsets of `DEFAULT_SPEC_POINTS`.
  `smoke4` = a diverse 4-config regression (single/multi controller,
  single/dual port, small/large geom). `full` = all 6 points.
  `--only <names>` / `--skip <names>` also select. `--list` prints and exits.
- `--rtl-only` — stop after the RTL step (fast; runs locally, see below).
- `--fresh` — `rm -rf` each workspace first (total wipe). `--clean <steps>` /
  `--clean-all` map to mflowgen's own `make clean-*` (keeps Makefile).
  `--skip-existing` skips workspaces with `done.flag`.
- `--make <targets>` — passthrough to `make` in each existing workspace
  (`status`, `list`, `runtimes`, `clean-<N>`, …). Output straight to terminal.
- `--parallel-jobs N` — `make -jN` within a build. `--config-jobs M` — build
  M configs concurrently (independent workspaces). Effective load ≈ M×N;
  mind RAM + Genus/Innovus licenses (2 configs × -j6 is a sweet spot).
- `--out-dir` (default `sweep_out/tile_memcore_pnr`) — **keep it OUTSIDE the
  garnet checkout.** `_preflight` hard-errors on a stale in-tree
  `garnet/sweep_out` because `gen_rtl` `docker cp`s the garnet tree into the
  build container and an in-tree mflowgen workspace holds absolute adk
  symlinks that `docker cp` rejects ("invalid symlink …").
- `--use-sim-sram` — behavioral SRAM instead of a hardened macro (for
  geometries with no matching physical macro).
- `--power` — after the build, run the **pre-synth (RTL) + post-synth**
  app-driven power flow instead of stopping at `--stop-after`. Sets
  `RTL_POWER=True` + `SYNTH_POWER=True` in the env (the construct reads them at
  graph-materialization time — they must be set *before* `mflowgen run`; either
  also disables power-aware PnR), then makes `post-rtl-power` +
  `post-synth-power`.
- `--include-pnr-power` — **additional, composable** flag that also makes the
  gate-level `post-pnr-power` leaf (post-signoff routed netlist). That node is
  *always* in the graph (no env toggle needed); this flag is what triggers
  building it. Use with `--power` for all three levels, or alone for just PnR
  power. Both power flags supersede `--stop-after`. Reports land under
  `*-tile-post-{rtl,synth,pnr}-power/reports/*.rpt`. Requires docker + Cadence +
  PrimeTime → build machine only. Typical full run (all three levels):
  `./mflowgen/sweep_specs.py --preset full --power --include-pnr-power
  --parallel-jobs 6 --config-jobs 2
  --out-dir /sim/mstrange/BUILD_CGRA/sweep_out/tile_memcore_pnr`.

## The Tile_MemCore graph — spec-specific pieces

`mflowgen/Tile_MemCore/construct.py` plus these session-added/-modified nodes:

- **`common/rtl/gen_rtl.sh`** — runs `garnet.py` (in the aha docker
  container when `use_container`) to emit `design.v`. Portable host paths:
  `GARNET_HOME` (required) + `LAKE_PATH` (defaults to `dirname($GARNET_HOME)/
  lake`). It `docker cp`s host garnet+lake into the container, then does
  `git fetch origin THESIS && git checkout -B THESIS origin/THESIS` on
  **/aha/lake inside the container** — so a pushed lake `THESIS` fix reaches
  the build without a manual lake pull on the build machine. Uses scoped
  `git config --global --add safe.directory /aha/{garnet,lake}` (copied-in
  repos are host-owned → "dubious ownership"). CAUTION: the whole container
  body is a host double-quoted `docker exec "..."` string — no `"`/`` ` ``/`$`
  in added comments or the string truncates.
- **`common/gen_sram_macro_spec/`** — RTL-driven SRAM macro build. Extracts
  the exact macro name from `design.v` (`get_macro_name.py`, regex fallback
  for uniquified `..._H_0_0` instances) and builds it via `IN12LP_MEM_
  genviews`. Selected in construct.py when `lake_spec_config` and not
  `use_sim_sram`.
- **`Tile_MemCore/constraints/constraints.tcl`** — mode case-analysis guard.
  The classic onyx MemCore has a 2-bit `mode[1:0]` bus; spec MemCores declare
  a 1-bit scalar `mode` (or none), so `set_case_analysis … mode[0]` aborts
  Genus with TUI-61. `_obj_exists` detects `mode[0]` once and skips the
  case-analysis when absent.
- **`Tile_MemCore/custom-init/outputs/floorplan.tcl`** — die-grow for tall
  spec macros. `core_height` is FIXED (tile must abut PE tiles), but a
  low-mux spec SRAM can be taller than that → macro at negative y →
  IMPSP-606 out-of-box → route overlaps. The grow branch measures the macro
  block and, only when it overflows the fixed height, grows height AND sizes
  width for macros + std cells (`total_cell_area/density + macro_area`),
  snapping to the site grid. Self-gated on the actual overflow (`lake_spec_
  config` env is NOT exported to the init step), so the default onyx build is
  byte-identical. Preferring `cols=2` macros (lake §5.1) keeps macros short,
  so most configs never trip the grow branch.

## Local RTL validation (no ADK/Cadence on /aha)

`/aha` has no docker/gf12-adk/Cadence, so synth/PnR need the build machine.
But garnet.py runs here, so RTL gen is verifiable locally in ~1 min/config.
See memory `reference_local_memcore_rtl_validation` and the scratch harness
that sweeps all 6 points' RTL gen (serial — garnet.py writes one
`garnet.v`; **with retry** for the flaky coreir SIGSEGV, lake §5.3).

## Helper scripts (build machine can't run Claude)

- **`watch_step.sh`** — follow the active mflowgen step live (auto-hops as
  steps advance; maintains a `current-step.log` symlink). `--symlink-only`,
  `--list`.
- **`logclip.sh`** — copy a build log to your LOCAL clipboard over ssh+tmux
  via OSC 52. Default = active step; `--all`, `--make`, `--step <NN-name>`,
  `--lines N`. Needs tmux `set-clipboard on` + `allow-passthrough on`.

## App-driven power (real Halide app → PrimeTime-PX)

Separate from the spec-MemCore sweep above: garnet/mflowgen has a flow that
runs a **real application** on the CGRA and computes its **dynamic power**.
Shared front of the chain (all under `common/`):

1. **`common/application/`** (`run.sh`) — runs the app in the
   `stanfordaha/garnet` container: `aha halide → aha map → aha test`, copies
   out `run.vcd` (real switching activity) + per-tile placement lists.
   Param `app_to_run` (default `tests/conv_3_3`).
2. **`common/testbench/generate_testbench.py`** — slices `run.vcd` into
   per-tile boundary stimulus + a self-checking `testbench.sv` (`$sdf_annotate`).
3. **`common/cadence-xcelium-sim/`** — sim → SAIF activity.
4. **`synopsys-ptpx-*/`** — `read_saif` + `report_power -hierarchy` →
   `outputs/power.hier`.

### Three power levels (which netlist the activity is annotated onto)

The tile builds can emit power at **three points in the flow**, each a
self-contained sub-graph (`common/tile-post-{rtl,synth,pnr}-power/`) wired into
`Tile_PE` / `Tile_MemCore` construct.py and driven all at once by
`sweep_specs.py --power`:

| Level | Node / ptpx flavor | Netlist powered | Node present when | Built by |
|---|---|---|---|---|
| **RTL** (pre-synth) | `tile-post-rtl-power` → `synopsys-ptpx-rtl` | signoff netlist, RTL-sim activity bound via `design.namemap` | `RTL_POWER=True` (else absent) | `--power` |
| **Synth** | `tile-post-synth-power` → `synopsys-ptpx-synth` | post-synthesis netlist | `SYNTH_POWER=True` (else absent) | `--power` |
| **PnR** | `tile-post-pnr-power` → `synopsys-ptpx-gl` | routed/signoff netlist (post-signoff — see below) | **always in graph** | `--include-pnr-power` |

- **RTL level is the earliest "run an app before synthesis" power.** It sims
  the RTL `design.v` to get switching activity, then powers the *signoff*
  netlist by `source`-ing `design.namemap` (Genus's RTL→gate name map) so the
  RTL-sim SAIF binds onto gate nodes. The namemap is **already** a first-class
  output of the ADK `cadence-genus-synthesis` step
  (`mflowgen/nodes/cadence-genus-synthesis/configure.yml` links
  `name_map.rpt → design.namemap`); `generate-results.tcl` just needs a **bare
  `write_name_mapping`** to emit `name_map.rpt` — do NOT redirect it to
  `results_syn/design.namemap` or you dangle that symlink.
- **PnR level is post-signoff.** `synopsys-ptpx-gl` sources from the signoff
  step (`design.vcs.v` / `design.spef.gz` / `design.pt.sdc`), which chains off
  `cadence-innovus-signoff ← postroute_hold`. Verified as genuinely
  post-signoff, not an intermediate.
- Setting `SYNTH_POWER` **or** `RTL_POWER` forces `pwr_aware = False` in the
  construct (power-aware/MMMC PnR is incompatible with the flat name mapping).

Entry points:
- **Fabric / multi-app:** `mflowgen/tile_array/` (design `Interconnect`)
  loops `e2e_apps = [tests/conv_3_3, apps/cascade, apps/harris_auto,
  apps/resnet_i1_o1_mem, apps/resnet_i1_o1_pond]`, cloning
  `e2e_testbench_<app>` → `e2e_xcelium_sim_<app>` → `e2e_ptpx_gl_<app>` per
  app (`set_param("app_to_run", app)`, `strip_path Interconnect_tb/dut`).
  `use_e2e=True` requires PWR_AWARE off / no flattening.
- **Single tile:** `Tile_PE` / `Tile_MemCore` construct.py wire
  `application → testbench → tile-post-{rtl,synth,pnr}-power` for one
  `app_to_run` (pnr always; rtl/synth when their env vars are set — see the
  three-level table above), so a tile build also emits that app's tile power.
  The pnr sub-graph can be driven directly via
  `common/tile-post-pnr-power/run_all_tiles.py` (iterates
  `inputs/tiles_<design>.list`); at sweep scope `--power` builds RTL+synth and
  `--include-pnr-power` adds PnR (see the sweep_specs flags above).

Gaps: **no full-chip app→dynamic-power** (`full_chip`/`soc` power steps are
power-grid/IR-drop only). The lake `pd/thesis` MemCore power flow is
**synthetic idle/active** bitstreams (`power-test-gen/`), not real apps.

## Build-machine note

The sweep runs from a **standalone** garnet checkout at
`/sim/mstrange/BUILD_CGRA/garnet` (with a sibling `lake`). aha gitlink bumps
do NOT update it — `git pull` there directly. Lake fixes flow via
origin/THESIS (gen_rtl checks it out in-container). Keep `sweep_out` out of
that checkout (docker-cp symlink breakage). See memory
`project_build_machine_standalone_garnet`.
