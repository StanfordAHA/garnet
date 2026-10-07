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
- `--spec-set {default,thesis}` — `default` = the 6 `DEFAULT_SPEC_POINTS`;
  `thesis` = `_thesis_spec_points()` (1:1 mirror of lake
  `ASPLOS_EXP/all_experiments_thesis_v2.sh`, the standalone synthesis set)
  ∪ those 6 → 107 unique specs. Unlike aha's `enumerate_thesis_configs()`,
  the 30 `max_sequence_width` points are kept (they share collateral but
  size the AG stride regs, so their RTL differs); names get `_msw<N>`.
- `--runtime-mode static,rv` — comma list; one config per (spec, mode).
  RV configs are named `<config>_rv` and get `LAKE_SPEC_MODE=rv` →
  `build_spec_rv`. Specs with `vec_width>1 && vec_capacity>2` are skipped
  for rv (committed `build_spec_rv` raises on them): thesis → 107 static +
  89 rv = 196 configs, 18 rv skipped. Static names are unchanged from older
  sweeps. Mode is a sweep-only key (`SWEEP_ONLY_KEYS`): it is stripped from
  `spec_config.json` because util_onyx passes that file to
  `build_spec(**spec)`; it lives in `sweep_meta.json` instead.
- `--pnr-set NAMES` / `--synth-stop` — per-config stop target: configs in
  `--pnr-set` (names and/or presets) build to `--stop-after` in their own
  pool of `--pnr-jobs` slots (default 1), concurrently with the
  `--config-jobs` pool of synth-only configs (so PnR neither takes the
  synth slots nor delays the synths; load = config_jobs + pnr_jobs); the
  rest stop at `--synth-stop` (default `cadence-genus-synthesis`). Names are checked against spec-set × modes
  before `--only/--skip/--preset`, so narrowed re-runs keep the same flag.
  `done.flag` records the targets (`ok <targets>`), so `--skip-existing`
  resumes a synth-only workspace that was later moved into `--pnr-set`.
- `--preset {smoke4,full,full_rv,full12}` — named subsets.
  `smoke4` = a diverse 4-config regression (single/multi controller,
  single/dual port, small/large geom). `full` = all 6 default points (static).
  `full_rv` = their RV twins; `full12` = both — the synth↔PnR correlation
  anchors. `--only <names>` / `--skip <names>` also select. `--list` prints
  names (stdout) + a mode/target summary (stderr) and exits.
- `--rtl-only` — stop after the RTL step (fast; runs locally, see below).
- `--fresh` — `rm -rf` each workspace first (total wipe). `--clean <steps>` /
  `--clean-all` map to mflowgen's own `make clean-*` (keeps Makefile).
  `--skip-existing` skips workspaces with `done.flag`.
- `--make <targets>` — passthrough to `make` in each existing workspace
  (`status`, `list`, `runtimes`, `clean-<N>`, …). Output straight to terminal.
- `--parallel-jobs N` — `make -jN` within a build. `--config-jobs M` — build
  M configs concurrently (independent workspaces). Effective load ≈ M×N;
  mind RAM + Genus/Innovus licenses (2 configs × -j6 is a sweet spot).
- Builds run with stdin = /dev/null (`_sh`). Before 2026-10-06 they inherited
  the terminal, so a Genus/Innovus script error left the tool at its
  interactive prompt and the sweep never returned (5 days on a route error).
  Now the tool reads EOF and exits, and the config is recorded FAIL.
- `--out-dir` (default `sweep_out/tile_memcore_pnr`) — **keep it OUTSIDE the
  garnet checkout.** `_preflight` hard-errors on a stale in-tree
  `garnet/sweep_out` because `gen_rtl` `docker cp`s the garnet tree into the
  build container and an in-tree mflowgen workspace holds absolute adk
  symlinks that `docker cp` rejects ("invalid symlink …").
- `--zip` / `--zip-only` / `--zip-path` — portable results archive for moving
  between machines. `--zip` runs after the sweep (even on failures);
  `--zip-only` archives an existing `--out-dir` and exits (all workspaces with a
  `spec_config.json`, or just the `--preset/--only/--skip` selection). Default
  path is next to out-dir: `<out-dir>_<host>_<timestamp>.zip`. Contents =
  `results.csv` + per-config JSON/logs/`done.flag`/per-step `mflowgen-run.log`
  + `ARTIFACT_GLOBS` reports, pulled straight from the workspaces (not
  `artifacts/`) so failed configs still contribute. No workspace DBs.
  Genus area/QoR live in `results_syn/final_*.rpt`, NOT `reports/`.
  Includes the SRAM macro datasheet (see `gen_sram_macro_spec` below) +
  `genviews_manifest.txt`; workspaces whose SRAM step predates the collector
  get theirs from `genviews-output/` (same match rule). Prints `SRAM macro
  datasheet: N/M` and names the configs without one.
- `--standalone-synth` / `--standalone-only` / `--correlate-only` —
  standalone-spec baseline for the standalone-synth → tile-synth → tile-PnR
  correlation. See "Standalone spec synth + correlation" below.
- `--memtile-power` — idle + active power of each spec MemTile (synth
  netlist always, signoff netlist for configs that run PnR) →
  `<out-dir>/memtile_power.csv`. See "MemTile idle/active power" below.

### Thesis-set synth sweep + synth→PnR projection (2026-09-30)

The run that motivated `--spec-set/--pnr-set`: every standalone-synthesis
spec inside the MemTile, static + RV, Genus synth for all, full PnR for the
12 `full12` anchors, to test whether tile synth area predicts tile PnR area
well enough to project PnR for the other 184 without building them:

    ./mflowgen/sweep_specs.py --spec-set thesis --runtime-mode static,rv \
        --pnr-set full12 --config-jobs 4 --pnr-jobs 2 --zip \
        --out-dir /sim/mstrange/BUILD_CGRA/sweep_out/tile_memcore_thesis

`correlation.csv` gains `runtime_mode`, `targets` and, per row,
`tile_pnr_{total,logic}_area_proj` (+ `_proj_fit` = which fit, `_proj_
extrapolated` = synth area outside the fitted range). `correlation_fit.csv`
holds the least-squares fits PnR = a + b·synth (stdlib, no numpy) for
`total` (Genus cell area → Innovus signoff instance total) and `logic`
(minus SRAM macros) over groups all/static/rv; a row uses its own mode's
fit when it has ≥3 points, else the pooled one. Instance area, not die:
the floorplan sizes the die from synth area (fixed height, width =
area/density), so die area adds no information. Re-run the analysis any
time with `--correlate-only`. Unit-tested on synthetic reports only.

**RTL-validated locally (2026-09-30):** all 196 configs generate tile RTL
(exact gen_rtl flags: `--width 4 --height 2 --pipeline_config_interval 8 -v
--glb_tile_mem_size 256 --no-pd --use-non-split-fifos [--dual-port]
--lake-spec-config … --lake-spec-mode …`) on committed garnet `8c5962fd` +
lake `origin/THESIS` `82a78497`, each with exactly one hardened macro family
(27 distinct; dual-port → SDPB). ~9% of `garnet.py` runs hit the flaky
native crash (SIGSEGV, or SIGABRT `malloc_consolidate(): invalid chunk
size`), mode-independent; 16/196 needed a retry, max 3 attempts. The
container path (`aha garnet`, `aha/util/garnet.py` `retry()`: 3× on
SIGSEGV/SIGBUS/SIGABRT) covers that; gen_rtl's NON-container path runs bare
`python garnet.py` with no retry. Gotcha for a pristine checkout (`git
archive`/fresh clone, non-container): `garnet.py` writes
`matrix_unit/header/matrix_unit_regspace.*` but git doesn't track the empty
dir → FileNotFoundError; `mkdir -p matrix_unit/header global_buffer/header
global_buffer/systemRDL/output global_controller/header
global_controller/systemRDL/output` first. Never validate in the shared
`/aha/garnet` (other sessions sim against its `garnet.v`/GLB headers) — use a
private copy.

Caveats:
- **Static tile RTL changed on 2026-10-01.** The static-MemCore fixes
  (config passthru instead of the 1976-bit config shadow reg, static-port
  FIFO bypass, static RAM/pond instead of the forced RV ones) landed in
  garnet `27da971d` + lake THESIS `ebd0948e`. Builds from before those
  commits carry the pre-fix static RTL (and the 196/196 RTL check above
  predates them); don't mix the two in one correlation.
- **Timing paths in the zip:** every tile synth writes the top-100 worst
  setup paths (one per endpoint) to `<step>/reports/Tile_MemCore.timing.
  setup.top100{,.summary}.rpt` (custom-genus-scripts/generate-results.tcl;
  legacy-UI `report timing -num_paths`, since `report_timing -max_paths`
  errors in this step's `common_ui false` Genus). Genus `final_time.rpt`
  has the top 50; PnR configs also get PT signoff's top-100 PBA setup/hold
  (`*-synopsys-pt-timing-signoff/reports/*.timing.{setup,hold}.rpt`).
- **No standalone RV synth exists.** lake's standalone builder
  (`thesis_sweep.py` → `build_four_port_wide_fetch`) forces
  `opt_rv = False` (its `--opt_rv` only switches the test vectors), and the
  experiment scripts never pass it. `--standalone-synth` skips `_rv`
  configs (SKIP row) instead of filing static RTL under an RV name.

### Standalone spec synth + correlation

`--standalone-synth` also builds each spec point through **lake's**
`pd/thesis` graph (bare `lakespec` from `tests/test_spec/thesis_sweep.py`,
no tile wrapper) up to `cadence-genus-synthesis`, in
`<out-dir>/standalone_synth/<config>/` (sibling tree — a nested dir inside the
tile workspace would be wiped by `make clean-all`). `--standalone-only` skips
the tile builds (add the baseline to a finished sweep). Graph kwargs mirror
lake's `ASPLOS_EXP/create_mflowgen_experiments.py`, but `python_command` calls
`thesis_sweep.py` directly with `sys.executable`. Lake comes from `--lake-dir`
(default `$LAKE_PATH`, else garnet's sibling `lake`), which the script puts
first on `PYTHONPATH` for the standalone mflowgen run/make — no `pip install
-e lake` needed, but lake's deps (kratos, magma, fault, networkx, …) must be in
the venv (build machine's `/home/mstrange/venv` has them). Preflight imports
`lake.spec.spec` and prints the real ImportError. On the build machine that
host lake needs `git pull` (gen_rtl's in-container THESIS checkout doesn't
cover it). `--standalone-rtl container` (opt-in, untested — no docker on
/aha) instead runs `thesis_sweep.py` via `standalone_spec_rtl.sh` in the aha
image at lake origin/THESIS, so standalone + tile RTL share one lake/kratos;
default host mode uses the venv's kratos, a possible correlation confound.

Every run (and `--correlate-only`/`--zip-only`) writes
`<out-dir>/correlation.csv`: per config, `{standalone_synth,tile_synth}_
{cell,total,sram,logic}_area` + `_wns_ps` + `_sram_macros` (Genus
`final_{area,gates,qor}.rpt`), and `tile_pnr_{total,macro,logic}_area`
(Innovus `signoff.area.rpt`) + `tile_pnr_setup_wns_ns` (PT
`*.timing.setup.rpt`). Parsers are fail-soft (blank cell). Validated against
lake's sample `signoff.area.rpt` and synthetic Genus/PT reports only — eyeball
the first real CSV.

Apples-to-apples caveats:
- **Clock:** tile `clock_period` is ns (`set_units -time ns`, 1.333 ≈ 750 MHz
  as of 2026-09-30; sweeps before that ran at 1.1); lake's is ps with no
  set_units. Standalone defaults to the tile's value ×1000 (1333 ps), read from
  `<--graph>/construct.py`; override `--standalone-clock-ps`. The 1.1 ns PnR
  sweep missed setup on all six `full` configs (In→Reg up to −128 ps).
- **SRAM macros differ:** standalone maps the full word onto ONE
  `GF_Tech_Map` macro (e.g. `W01024B064`); the tile's CoreCombiner prefers 2
  half-width columns (2× `W01024B032`). Compare `*_logic_area`, and check the
  `*_sram_macros` columns.
- **Storage placement:** `thesis_sweep` builds `remote_storage=False` (SRAM
  inside `lakespec`); garnet's `build_spec` uses `remote_storage=True` (SRAM in
  the MemoryTileBuilder wrapper, shared with StrgRAM + StencilValid). Tile synth
  also includes the SB/CB interconnect.
- **Lake graph needed fixes (2026-09-29):** `mflowgen run` on `lake/pd/thesis`
  had been failing since the roundtrip nodes landed (`25a9c33b`):
  `synopsys-vcs-sim-synth` lacked a `testbench.sv` input, and the two
  `clockwork-roundtrip-sim-*` steps had unescaped `{`/`}` (mflowgen formats
  commands — use `{{`/`}}`).
- `--use-sim-sram` — behavioral SRAM instead of a hardened macro (for
  geometries with no matching physical macro).
- `--cgra-power` (alias `--power`) — after the build, run the **pre-synth
  (RTL) + post-synth** app-driven power flow instead of stopping at
  `--stop-after`. **Not usable for lake-spec configs yet:** the `application`
  step runs the app on the *default* MemCore in the stock
  `stanfordaha/garnet:latest` container (no spec flags, upstream aha/clockwork,
  2020-era VCD/place paths), so the stimulus replayed into the spec tile is
  wrong and the power numbers are meaningless. Plain PnR sweeps (no power flag)
  are unaffected. Sets
  `RTL_POWER=True` + `SYNTH_POWER=True` in the env (the construct reads them at
  graph-materialization time — they must be set *before* `mflowgen run`; either
  also disables power-aware PnR), then makes `post-rtl-power` +
  `post-synth-power`.
- `--include-pnr-power` — **additional, composable** flag that also makes the
  gate-level `post-pnr-power` leaf (post-signoff routed netlist). That node is
  *always* in the graph (no env toggle needed); this flag is what triggers
  building it. Use with `--cgra-power` for all three levels, or alone for just PnR
  power. Both power flags supersede `--stop-after`. Reports land under
  `*-tile-post-{rtl,synth,pnr}-power/reports/*.rpt`. Requires docker + Cadence +
  PrimeTime → build machine only. Typical full run (all three levels):
  `./mflowgen/sweep_specs.py --preset full --cgra-power --include-pnr-power
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
  `use_sim_sram`. Then `check_sram_period.py` fails the step if
  `clock_period` (ns, via `update_params`) is shorter than the macro's
  minimum cycle time at `$corner` (TT), or half of it is under the min clock
  high/low. Source: the genviews datasheet `genviews-output/doc/
  <macro>_<corner>.csv` ("Clock Cycle Time"), else the lib's CLK
  `minimum_period` checks — one per `MA_VD*` state, uncharacterized ones are
  `999999` placeholders and are dropped. Unparseable → warns and passes.
  Result in `reports/sram_period.rpt` (zipped). E.g. S1DB `W02048B008M16S2`
  is 437 ps TT / 594 ps SSPG, far under the 1.333 ns target. The datasheet
  CSVs are Synopsys-confidential: never commit them (garnet is public).
  `collect_datasheet.py` (2026-10-01) links the
  compiler's datasheet into `outputs/sram_datasheet/` and lists every file
  genviews wrote in `genviews_manifest.txt` (+ the compiler's `-help` when no
  datasheet matched). The compiler writes one CSV per corner at
  `genviews-output/doc/<macro>_<corner>.csv` (the file check_sram_period.py
  reads); the match takes everything under `doc/`, with `*datasheet*` and
  `.ds/.pdf/.html` as fallbacks (checked on that layout 2026-10-06; no ADK on
  /aha, so the first build-machine manifest is still worth a look).
  Fail-soft (never fails the step). Runs before check_sram_period.py, so a
  too-fast clock still leaves the datasheet behind.
  Deliberately NOT a declared mflowgen output: mflowgen stamps each declared
  output (`outputs/.execstamp.<name>`), so a new one would make every existing
  workspace re-run gen_sram and all of synth/PnR on its next make. The fixed
  `gen_sram_macro` (default/`use_sim_sram`) step collects no datasheet.
- **`Tile_MemCore/constraints/constraints.tcl`** — mode case-analysis guard.
  The classic onyx MemCore has a 2-bit `mode[1:0]` bus; spec MemCores declare
  a 1-bit scalar `mode` (or none), so `set_case_analysis … mode[0]` aborts
  Genus with TUI-61. `_obj_exists` detects `mode[0]` once and skips the
  case-analysis when absent.
- **`Tile_MemCore/constraints/common.tcl`** — `clk_out` max delay. The
  blanket `set_output_delay … [all_outputs]` (0.1×period) also lands on
  `clk_out`, so the old `set_max_delay -to $pt_clk_out 0.05` left a bare wire
  at −60 ps in every Genus run at 1.1 ns (and worse at slower clocks). The max
  delay is now `clock_max_delay + o_delay`, matching Tile_PE, so the 50 ps
  budget is the feedthrough's own (2026-09-30).
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
- **`Tile_MemCore/pre-route/`** — lake-spec builds only (the default onyx
  graph is unchanged). Supplies `pre-route.tcl`, sourced first in the route
  step's `order` (after the design restore, before `run_route.tcl`'s
  `addFiller` + `routeDesign -placementCheck`); same hook as
  `full_chip/pre-route`. It sets `setFillerMode -fitGap true` (in a `catch`)
  so addFiller can move a cell to close 1-site gaps: GF12's smallest filler
  is 2 sites, so an unremovable 1-site gap is an unfillable FillerGap and
  routeDesign aborts with NRIG-76. Seen 2026-10-01 on static
  `fw4_dw16_sc8192_dp_in4_out4_vc2` at 1.333 ns (5 unfilled sites). Every
  route log shows the second "addFiller without DRC checking" pass placing
  DRC-violating `FILL_incr` cells — those routed fine but are a latent
  signoff-DRC issue.

## Local RTL validation (no ADK/Cadence on /aha)

`/aha` has no docker/gf12-adk/Cadence, so synth/PnR need the build machine.
But garnet.py runs here, so RTL gen is verifiable locally in ~1 min/config.
See memory `reference_local_memcore_rtl_validation` and the scratch harness
that sweeps all 6 points' RTL gen (serial — garnet.py writes one
`garnet.v`; **with retry** for the flaky coreir SIGSEGV, lake §5.3).

## MemTile idle/active power (`--memtile-power`, 2026-10-01)

Lake's standalone idle/active power tests (`lake/pd/thesis/power-test-gen`,
which drive a bare `lakespec`) ported to the whole `Tile_MemCore`, so every
sweep spec gets an idle and a max-activity power number for the tile as it
sits in the CGRA. `MEMTILE_POWER=True` (set by the flag) adds to the graph:

- `memtile-power-test-gen` (`common/memtile-power-test-gen/`): rebuilds the
  CGRA in Python with the rtl step's exact garnet.py flags (container: same
  image, host garnet+lake copied in, lake at origin/THESIS, like gen_rtl;
  `use_container=False` runs in `$GARNET_HOME` like gen_rtl's host path), takes
  the first MEM tile and emits `testbench.{idle,active}.sv`, `input_data.hex`
  and `power_tests.json` (tile, routes, input tracks, port programs, config
  writes, window). Needs lake with `lake/utils/power_test_programs.py` (the
  container takes lake origin/THESIS, so it must be pushed there).
  Config goes in through the tile's own config bus: routes from canal
  (`get_route_bitstream`), core config via `configure_placement` with the
  spec's `gen_bitstream` forced to `over=True` (our program is already
  port-level), merged per address with gemstone `compress_config_data`.
  Routing: a 16-bit spec port is one 17-bit core pin -> input k on WEST
  track k, output k on EAST track k (pipeline reg bypassed). Any other data
  width (dw 8/32/64 thesis points, ~20% of the set) is BIT-BLASTED by
  MemoryTileBuilder onto 1-bit core pins `port_<i>_<bit>` (+ 1-bit
  `port_<i>_valid/_ready`) -> data bits spread over the 20 1-bit tracks
  (shared once they run out: correlated but toggling), valid/ready pins on one
  track held at 1, the unused comply_17 MSB on a quiet track; output bits take
  free 1-bit SB_OUTs, interleaved across ports, the rest unobserved. Unused SB
  outputs and CBs whose default source is a random track get their select
  moved to a static one -- an undriven track, else the track held at 1
  (bit-blasted specs drive nearly every 1-bit track) -- select only, no RV
  `_enable`; any left on a random source are listed as `unquieted_muxes`
  in power_tests.json.
- `memtile-power-sim-{synth,pnr}-{idle,active}` (`common/memtile-power-sim/`):
  xrun (or VCS, param `tool`) on the Genus netlist / signoff `design.vcs.v` +
  gen_sram `sram.v` + adk stdcells. Reset with flush high, config writes,
  flush release, then a SAIF over `window` cycles only (Xcelium: tb `$stop`s
  + `cmd.tcl` `dumpsaif`; VCS: `$toggle_*`). The step FAILS unless the tb
  prints `MEMTILE_POWER_TEST <variant> PASS` (idle: no SB data output moves;
  active: every routed output changes ≥ half the elements the program should
  deliver) — a broken stimulus never produces a power number.
- `memtile-power-{synth,pnr}-{idle,active}`: the stock
  `synopsys-ptpx-synth` / `synopsys-ptpx-gl` (+ `sram_tt.db`), strip path
  `testbench/dut`.

Stimulus (2026-10-06; user decisions): programs + input data come from lake
`lake/utils/power_test_programs.py`, shared with lake's standalone power tests
(`pd/thesis/power-test-gen`) -- same spec + `seed` -> same programs and the
same input words per cycle in both flows. Idle and active get the SAME
stimulus (routes, valid/ready, data); only the spec program differs, so
active − idle is the memory's own work.
- **input data** = a fresh random `data_width`-bit word per spec input port
  per cycle from flush release (`input_streams`, `input_data.hex`, read by
  the tb; track-major). 16-bit ports: the word on the 17-bit track (bit 16 =
  unused comply_17 bit, 0); bit-blasted ports: bit b of the word on its
  track (a shared track carries its first pin's bit).
- **idle** = the empty application (tile_en=1, lakespec mode, all controllers
  cleared) with the stimulus applied: no port fires, every switch-box data
  output must stay quiet. (An unconfigured tile — tile_en=0 — is NOT
  measured.)
- **active, static spec** = maximum *sustainable* traffic: every port moves
  one SRAM word per period P and streams its fw elements at one per cycle;
  P = fw when the memory keeps up, else the number of ports sharing a memory
  port (SP: in+out, DP: max(in, out)); SRAM accesses slotted so the memory
  port(s) are busy every cycle. Readers re-read what their writer stored 2
  words earlier (RTL-checked: outputs replay the input stream 16 cycles
  later). Within-word timing = lake's static wide-fetch linear test. The
  first standalone program (overlapping SIPO/PISO schedules: outputs moved
  2–4 times in 1000 cycles) was replaced by this one on both sides.
- **active, RV spec** = lake `test_spec_rv_programs` `stream`: writer i →
  reader i trailing by the zero-lag margin `2*fw*vc+4`, dependence at level
  0; valid/ready held high on the routed pins. 1-dimensional specs can't take
  that (lake refuses non-barrier constraints at the top level of a
  power-of-2-dims domain; without one the reader races over unwritten words):
  they run `barrier` instead -- writers, then readers -- both phases sized to
  the window.
- Domains are sized from the generated HW (`2**extent_width`, SG stride
  width); a spec that cannot keep its ports busy for `sim_cycles` (e.g.
  dims=1, max_extent=64) gets a shorter window, recorded in
  `power_tests.json` and `memtile_power.csv` (`*_window_cycles`).

The sweep makes the power leaves in a SECOND make after the config's build
targets (`make_memtile_power.log`): a power failure is a note on a PASS row
(`memtile_power_failed(...)`) and leaves done.flag at the build targets, so
`--skip-existing` retries only the power leaves.

`memtile_power.csv` (written with correlation.csv, also by
`--correlate-only`): per config, `{synth,pnr}_{idle,active}_{internal,
switching,leakage,total}_power` (PT report units) + `*_active_over_idle`.

Validated on /aha (2026-10-01, tile RTL from garnet.py `--use_sim_sram`):
idle + active PASS for 21 spec×mode points -- static and RV; SP and DP; fw
1/2/4/8; 1×1, 2×2, 4×4; dw 8/16/32/64 (bit-blasted); dims 1/2/4/6 with
max_extent 64/256 and max_sequence_width 64 -- under xrun (VCS too for fw4
2×2: same results, SAIF root `testbench/dut`, 1000-cycle window). Active
outputs stream at the program's rate (16-bit outputs ~980/1000 cycles at P=fw)
and fw4 2×2 outputs replay the input stream exactly (16-cycle latency). Graph
materializes with the right wiring (stub ADK, `PYTHONPATH=garnet/mflowgen`);
`make memtile-power-test-gen` passes in a real workspace (host mode).
2026-10-06 (shared programs + random streams): standalone (thesis_sweep RTL,
VCS, validate_sim.py) fw4 SP 2×2 / fw2 DP 2×2 / fw1 SP 1×1 idle + active PASS,
active outputs stream (≈986/1000, 996/1000, 498/1000 = P 2); tile fw4 SP 2×2
static+RV, fw2 DP 2×2, fw4 dw8/dw32 static, fw4 dw32 RV, 1-D RV idle + active
PASS; fw4 SP 2×2 tile input tracks = the standalone streams word for word
(1064/1064). lake `pd/thesis` graph materializes (it did NOT before: the
power sims were fed an undeclared `testbench.sv`) and `make power-test-gen`
passes on a 2-D max_extent-64 spec.
NOT run here: gf12 synth/signoff netlists, gen_sram `sram.v`, adk cell models,
ptpx (no ADK) and the docker path — check the first build-machine run's
`*-memtile-power-sim-*/logs/sim.log` PASS lines and power reports.

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
`sweep_specs.py --cgra-power`:

| Level | Node / ptpx flavor | Netlist powered | Node present when | Built by |
|---|---|---|---|---|
| **RTL** (pre-synth) | `tile-post-rtl-power` → `synopsys-ptpx-rtl` | signoff netlist, RTL-sim activity bound via `design.namemap` | `RTL_POWER=True` (else absent) | `--cgra-power` |
| **Synth** | `tile-post-synth-power` → `synopsys-ptpx-synth` | post-synthesis netlist | `SYNTH_POWER=True` (else absent) | `--cgra-power` |
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
  `inputs/tiles_<design>.list`); at sweep scope `--cgra-power` builds RTL+synth and
  `--include-pnr-power` adds PnR (see the sweep_specs flags above).

Gaps: **no full-chip app→dynamic-power** (`full_chip`/`soc` power steps are
power-grid/IR-drop only). The lake `pd/thesis` MemCore power flow is
**synthetic idle/active** bitstreams (`power-test-gen/`), not real apps.

## PE-tile pond knobs (Tile_PE with / without / spec pond) (2026-09-30)

`Tile_PE` uses the same shared `common/rtl` step as Tile_MemCore (whole-chip
`garnet.py` → synth picks the `Tile_PE` top), so it builds on the build machine
as-is; none of the MemCore-specific nodes (spec SRAM macro, die-grow
floorplan, `mode[0]` guard) apply — the pond is flops, no macro.

- `NO_POND=True mflowgen run --design .../Tile_PE` → rtl param `no_pond` →
  `garnet.py --no-pond`. **`--no-pond` never worked in onyx before
  2026-09-30**: `get_cc_args` had `args.add_pond = not args.no_pond,` (trailing
  comma → 1-tuple → always truthy); fixed. The same bug is still on
  `args.add_pd = not args.no_pd,` → `--no-pd` (passed whenever PWR_AWARE is
  False, incl. every MemCore sweep build) is a no-op; NOT fixed because fixing
  it changes existing RTL — user decision.
- `LAKE_POND_SPEC_CONFIG=<pond.json> mflowgen run ...` → rtl param
  `lake_pond_spec_config` → `garnet.py --lake-pond-spec-config` (env
  `LAKE_POND_SPEC_CONFIG`; gen_rtl ships the file into the container like
  `lake_spec_config`). In `cgra/util_onyx.py` `make_pond()`: set → a lake-spec
  pond in both modes (`build_pond` static / `build_pond_rv` in RV mode), sized
  from the JSON; `{}` = default geometry (64 B, 4 dims). Keys: `storage_capacity`,
  `dims`, `data_width` (must be 16 = fabric), static also `max_extent`,
  `max_sequence_width`; unknown keys raise. Unset → unchanged: RV spec pond in
  RV mode, legacy `PondCore` otherwise (static spec pond is opt-in until a
  full-CGRA app run validates it). The static spec pond drops the legacy
  1-bit valid → PE `bit0` inter-core wire.
- Verified locally (private garnet copies, 4x2): no-flag builds unchanged
  (static-spec byte-identical; RV identical up to one module's position in the
  file; default differs only by pre-existing kratos nondeterminism in the sparse
  MemCore FSMs, which differs between two runs of the same code even with
  `PYTHONHASHSEED=0`); `--no-pond` removes the pond from Tile_PE; spec ponds
  elaborate with the requested geometry; garnet's `CoreCombinerCore`
  `get_config_bitstream` takes clockwork's static pond instrs (8 real configs).
- The pond spec is built by lake's `build_cgra_pond` (single factory shared with
  the pond's compiler collateral, `lake.utils.pond_collateral`); the static pond
  defaults to 16-bit iteration ranges like the legacy pond. Compiler side: clockwork
  takes the pond as its `regfile` level from `LAKE_COLLATERAL_JSON_REGFILE`
  (`aha map --pond-collateral`, or auto from `LAKE_POND_SPEC_CONFIG`); see
  `/aha/clockwork/CLAUDE.md` "Pond (regfile level)". Without a pond collateral,
  clockwork assumes the default 32-word / 4-level pond. The RV pond has input
  filter hardware by default (broadcast-banked weight ponds).
- GOTCHA for private garnet trees: `garnet.py --verilog` writes the GLB / GLC /
  matrix-unit headers under `$GARNET_HOME` (env default `/aha/garnet`, the shared
  tree), not next to itself — pin `GARNET_HOME` to the private copy or the build
  rewrites the shared headers other sessions simulate against.

## Build-machine note

The sweep runs from a **standalone** garnet checkout at
`/sim/mstrange/BUILD_CGRA/garnet` (with a sibling `lake`). aha gitlink bumps
do NOT update it — `git pull` there directly. Lake fixes flow via
origin/THESIS (gen_rtl checks it out in-container). Keep `sweep_out` out of
that checkout (docker-cp symlink breakage). See memory
`project_build_machine_standalone_garnet`.
