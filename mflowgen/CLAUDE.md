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
target chain up to `--stop-after` (default `synopsys-pt-timing-signoff` since
2026-10-07; before that `cadence-innovus-signoff`, which never ran PT, so
older sweeps have blank `tile_pnr_setup_wns_ns` -- see "PT signoff" below).
Results (pass/fail, macro, workspace) go to `<out-dir>/results.csv`.

Key flags:
- `--spec-set {default,thesis}` — `default` = the 6 `DEFAULT_SPEC_POINTS`;
  `thesis` = `_thesis_spec_points()` (1:1 mirror of lake
  `ASPLOS_EXP/all_experiments_thesis_v2.sh`, the standalone synthesis set)
  ∪ those 6 → 107 unique specs. Unlike aha's `enumerate_thesis_configs()`,
  the 30 `max_sequence_width` points are kept (they share collateral but
  size the static ScheduleGenerator's stride regs, so their RTL differs);
  names get `_msw<N>`. RV ignores it: lake `build_spec_rv` computes
  `stride_width` but `ReadyValidScheduleGenerator` takes none (and no
  AddressGenerator takes it in either mode), so the 30 `_msw*_rv` configs are
  6 distinct designs, one per dims (identical area in the 2026-10-06 sweep).
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
  datasheet: N/M` and names the configs without one. Speed (2026-10-06): a
  top-level `make*.log` over 4 MB goes in as its last 2000 lines (it is make's
  stdout = every step log again via mflowgen's tee, plus make's own lines and
  the postcondition results), files >= 16 MB (merged GDS, Innovus logs) are
  deflated at level 1, `.gz`/... are stored; prints the input size up front,
  a progress line every 30 s, the elapsed time at the end. Synthetic 2-config
  PnR-shaped benchmark: 99 s -> 24 s, 543 -> 463 MB.
- `--zip-slim` (2026-10-07) — with `--zip`/`--zip-only`: skip the signoff
  layout/library views (`LAYOUT_GLOBS`: merged GDS, LEF, LIB = most of a PnR
  config's bytes; nothing parses them), name gets `_slim`. Everything the
  CSVs, lake `THESIS/pipeline/tile_sweep.py` and the follow-up analyses read
  stays. **Pulling results to /aha** (the build machine can't reach /aha;
  the user copies files over): on the build machine, any time, also while
  the sweep runs (read-only on the workspaces; rewrites only the out-dir
  CSVs) `./mflowgen/sweep_specs.py --zip-only --zip-slim --out-dir <dir>`,
  then copy `<dir>_<host>_<ts>_slim.zip` into `/aha/sweep_out/`. PT's
  `reports/*.report` (global timing, check_timing, ...) are zipped too.
- `--standalone-synth` / `--standalone-only` / `--correlate-only` —
  standalone-spec baseline for the standalone-synth → tile-synth → tile-PnR
  correlation. See "Standalone spec synth + correlation" below.
- `--memtile-power` — idle + active power of each spec MemTile (synth
  netlist always, signoff netlist for configs that run PnR) →
  `<out-dir>/memtile_power.csv`. See "MemTile idle/active power" below.
  With `--standalone-synth` it also runs lake's standalone idle/active power.
- `--also-make TARGETS` — extra tile targets (genlibdb, DRC, LVS, ...) made
  last; failure is a note. See "Whole-graph smoke run" below.
- `--flatten-effort N` (2026-10-07) → env `FLATTEN` → Tile_MemCore
  `flatten_effort` (construct default still 3; Tile_PE already read `FLATTEN`).
  The Genus node only tells 0 (`auto_ungroup none`: hierarchy kept, as lake's
  standalone `pd/thesis` synth runs) from non-zero (`auto_ungroup both`).
  Tile builds before this flag were all flattened while the standalone synths
  kept hierarchy — a standalone-vs-tile synth confound in older correlations.
  Checked locally (Genus 20.11 + Innovus 23.1, freepdk45 toy design): with 0
  the area report keeps per-instance rows (top row first, so the correlation
  parsers are unchanged); floorplan.tcl's `get_property [get_cells *] area`
  returns top-level hinsts with their summed leaf area, so die sizing is
  unchanged; `dbGet -p top.insts.name *<leaf>` can match several hinsts, but the
  tile's SRAM leaf names (`..._H_0_0`, `_H_1_0`, one MemCore) stay unique.
- `--data-width 16[,32]` — keep only specs of those widths (before presets and
  --pnr-set/--validate-set name checks).
- `--validate-set NAMES` — PnR configs held OUT of the synth→PnR fits; their
  PnR area + idle/active power are predicted and compared in
  `pnr_validation.csv` (see the dw16 section below). Stored as `pnr_role` in
  sweep_meta.json, so `--correlate-only` reproduces the split (the flag there
  overrides it).
- `build_manifest.json` in every tile/standalone workspace: argv + every
  parsed flag, the env knobs exported (`settings`), spec, targets, git state
  of garnet/lake (+ host `origin/THESIS`)/mflowgen at sweep start, and every
  step's parameters as resolved by `mflowgen run` (the `export` lines of
  `.mflowgen/<step>/mflowgen-run`); finished with status, executed steps and
  the rtl step's `aha garnet` flags + lake commit (container mode). Zipped.
- Stale steps / `--clean-stale`: mflowgen's make rules don't depend on step
  parameters, so a finished step is NOT rebuilt when only its params change
  (e.g. a new `--flatten-effort` on an existing workspace). After `mflowgen
  run` the sweep diffs each executed step's own `mflowgen-run` (copied in when
  it ran) against `.mflowgen/`'s and FAILS the config listing `step: param
  old->new`; `--clean-stale` instead `make clean-<N>`s those steps (downstream
  rebuilds by timestamp). `--skip-existing` only skips a done workspace whose
  manifest `settings` match (no manifest → skips as before). Expect this to
  fire when resuming workspaces built before a garnet change to a step's
  params (e.g. d4fc47e3 changed init/route `order`). A failed `mflowgen run`
  or stale check puts the workspace's previous Makefile/.mflowgen back
  (`_materialize_graph`, backup in `.mflowgen.prev`), so the workspace keeps
  the graph its steps were built with. Sweeps 2026-10-07 fb50802c..2ea43d98
  lacked that restore: a plain re-run there already overwrote the graph.
- `--reuse-graph`: in a workspace with a Makefile, skip `mflowgen run` and make
  against the graph it was built with (manifest `graph_reused: true`; a
  target that graph lacks fails that config only). For adding a step to an
  old sweep without the current graph's changes rebuilding finished steps.

### PT signoff (default stop target since 2026-10-07)

`synopsys-pt-timing-signoff` (stock mflowgen node + `sram_tt.db`) is
PrimeTime STA on the routed result: it links the signoff netlist
(`design.vcs.v`) against the ADK stdcell .db + SRAM .db, reads the SDC
Innovus wrote (`design.pt.sdc`, derived from our constraints), reads the
extracted RC (`design.spef.gz`), `update_timing -full`, and writes
check_constraints/check_timing/global timing/clock skew/coverage reports,
the top-100 setup and hold paths with exhaustive path-based analysis
(`<design>.timing.{setup,hold}.rpt`; correlation.csv's `tile_pnr_setup_wns_ns`
= the worst setup slack there), and `design.sdf` (back-annotated delays for
gate-level sim). It consumes constraints, it doesn't make them, and changes
nothing in the design. The BUILD MACHINE's mflowgen PT node differs from
/aha's copy (`/aha/mflowgen/nodes/...`): it links only `inputs/adk/
stdcells.db` + `sram_tt.db` (one typical corner, so hold is checked at
typical too) and loads the SDC with `read_sdc -echo` (SDC commands only --
hence `fix-pt-sdc.tcl` below), where /aha's copy `source`s it and puts the
typical + bc libs on the link path. Read the step's mflowgen-run.log, not
/aha's node, to see what ran. Innovus signoff also times the design: its
main.tcl sources the foundation flow's `run_signoff.tcl` (generated by
flowsetup on the build machine, not in this repo), whose timing summary is
`reports/signoff.summary` (zipped) -- the per-path-group WNS in the
thesis-run result above came from there. correlation.csv has it as
`tile_pnr_innovus_wns_{all,reg2reg,in2reg,reg2out,in2out}_ns` (2026-10-08;
"Setup mode" table, N/A = no paths), next to PT's `tile_pnr_setup_wns_ns`. On
the 2026-10-07 smoke run: Innovus all -0.090 (in2out), reg2reg -0.000; PT
-1.229 from the truncated SDC.

**Don't backfill PT on a sweep whose signoff ran before 618adedd** (any sweep
from before 2026-10-08, e.g. the thesis run). `--skip-existing --reuse-graph`
would make only PT against the workspace's own graph, but that graph's signoff
wrote the unfixed `design.pt.sdc` (no `fix-pt-sdc.tcl`) and has no "Errors
reading SDC" guard, so PT silently reads the truncated SDC again. For timing on
such sweeps use `--correlate-only`: it fills `tile_pnr_innovus_wns_*_ns` from
the existing `signoff.summary`. Sweeps whose graph already has the fix can
add PT with `--skip-existing --clean-stale` (a newer garnet re-runs signoff
onward). `--reuse-graph` itself was checked on a scratch graph that changed a
built step's params and inputs: plain re-run → stale FAIL + graph restored;
`--reuse-graph` → only the new target runs, upstream outputs untouched;
`--clean-stale` → adopts the new graph and rebuilds.

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

**Result (zip `tile_memcore_thesis_r8cad-gf12_20261006-221414`, 2026-10-06):**
all 196 configs synthesized and all 12 `full12` anchors through signoff
(flattened, 1.333 ns). Synth meets timing except the
three `fw2_dw64_*` builds (−7…−10 ps). Every PnR anchor misses setup (WNS −13…
−229 ps, mostly In2Reg/In2Out; Reg2Reg ≥ −76 ps). Innovus/Genus std-cell area
is 1.05–1.10× (fit 1.082·synth − 72 µm²). Last failures, now fixed: static
`fw4_dw16_sc8192_dp_in4_out4_vc2` route (NRIG-76 → `fix-tap-gaps.tcl` below) and
`fw1_dw16_sc8192_sp_in2_out2_dim1_msw256_rv` RTL gen (flaky SIGSEGV; passed on
re-run). Ingested by lake `THESIS/pipeline/tile_sweep.py` (lake CLAUDE.md §1.8).
RTL lake commit is mixed — each rtl log prints the commit it checked out on the
line after `Mek Mek Mek`/`Reset branch 'THESIS'`. `82a78497` (pre static fix):
all PORT_EXP, ITERATION_DOMAIN_EXP, default points and all 12 PnR anchors, 47
of 60 AFFINE. `ebd0948e`: all MEMORY_EXP, 12 AFFINE (dims 6, + dims 5 at the
largest msw). `577c6beb`: the 10-06 re-run of `..._dim1_msw256_rv`, +4.5%
std-cell area over its 82a78497 neighbors. AFFINE static shows no step
between 82a78497 and ebd0948e builds. A fresh `--out-dir` (as the dw16 plan
below uses) rebuilds every config at one lake commit.

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

### dw16 synth sweep + held-out PnR validation (2026-10-07)

User plan: other data widths aren't at parity yet, so a good synth sweep of the
16-bit thesis specs (hierarchy kept, idle/active power) with 12 PnR builds: 8
fit the synth→PnR model, 4 are held out to validate its predictions.

    ./mflowgen/sweep_specs.py --spec-set thesis --data-width 16 \
        --runtime-mode static,rv --flatten-effort 0 --memtile-power \
        --pnr-set dw16_pnr12 --validate-set dw16_val4 \
        --config-jobs 4 --pnr-jobs 2 --zip --out-dir <NEW dir>

172 configs (89 static + 83 RV; 6 RV skipped, fw>1 & vc>2). 108 of them are
one cluster — fw1 sp 2×2 sc8192, varying dims × max_extent/max_sequence_width
— which `full12` never touches. Presets: `dw16_fit8` = fw1 sp 1×1 sc4096, fw2
dp 2×2 sc4096, fw4 sp 2×2 sc8192, fw8 sp 4×4 sc32768, each static + RV (4 per
mode, so each mode gets its own fit; MIN_FIT_POINTS = 3). `dw16_val4` = two
cluster points (`..._me4096` static, `..._dim4_msw1024_rv`), fw4 dp 4×4 RV,
fw4 sp 2×2 vc4 static. Picked by structure (no dw16 synth data existed);
`_proj_extrapolated` flags a held-out point outside its fit's synth range.

Outputs (also from `--correlate-only`): correlation.csv gains `pnr_role`,
`*_proj_err_pct` (fit rows: residual; validate rows: prediction error) and
`tile_pnr_total_area_proj_via_logic` = synth SRAM macro area + the `logic`
fit (macros carry over unchanged, so their area isn't scaled by a fitted
slope the way the direct `total` fit scales it); correlation_fit.csv gains
`val_n/val_mean_abs_pct_err/val_max_abs_pct_err`. memtile_power.csv now
projects `pnr_{idle,active}_total_power` from the synth-netlist power the same
way (memtile_power_fit.csv). `pnr_validation.csv`: per held-out config ×
{total_area, total_area_via_logic, logic_area, idle_power, active_power} the
synth value, predicted PnR, actual PnR, error. Validated only on synthetic
reports (fits match numpy; roles, override, legacy no-role out-dir) + stub-ADK
graph materialization. Unchecked until real data: Genus SRAM area (.lib) vs
Innovus macro area (LEF) — via_logic assumes they're equal; compare
`tile_synth_sram_area` with `tile_pnr_macro_area` in the first real CSV.

### Whole-graph smoke run: one spec, standalone + tile (2026-10-07)

To check the flow end to end before a big sweep (user request), one static
config: `fw4_dw16_sc4096_sp_in2_out2_vc2` = lake `build_spec()` defaults = the
default onyx MemCore geometry (64-bit × 512 words, fw4, 2 in / 2 out):

    ./mflowgen/sweep_specs.py --spec-set thesis --only fw4_dw16_sc4096_sp_in2_out2_vc2 \
        --flatten-effort 0 --memtile-power --standalone-synth \
        --stop-after synopsys-pt-timing-signoff \
        --also-make synopsys-ptpx-genlibdb,synopsys-dc-lib2db,drc,lvs,drcplus-pm \
        --parallel-jobs 6 --zip --out-dir <new dir>

Tile: make `synopsys-pt-timing-signoff` (rtl → SRAM → synth → PnR →
signoff → PT), then `memtile-power-{synth,pnr}-{idle,active}`, then the
`--also-make` targets. Standalone (lake pd/thesis, host `--lake-dir`):
`cadence-genus-synthesis`, then `synopsys-ptpx-synth-{idle,active}-power`.
- `--also-make` (new): extra tile targets in a third make (`make_also.log`);
  failure = row note `also_make_failed(...)`, done.flag keeps the build
  targets so `--skip-existing` retries them. A name that isn't a step resolves
  to the one numbered step ending in `-<name>` (`drc`/`lvs` → mentor-calibre-*
  if `calibre` is on PATH at `mflowgen run`, else cadence-pegasus-*;
  `debug-<step>` targets excluded). Resolved right after `mflowgen run`, so a
  bad name fails before the build. DRC postconditions don't check violation
  counts; LVS fails on `INCORRECT`.
- `--memtile-power` + `--standalone-synth` (new) also makes lake's standalone
  idle/active power leaves (second make, `make_power.log`, failure = note;
  standalone done.flag now `ok <targets>`, a bare `ok` = synth only) →
  `standalone_{idle,active}_*_power` + `standalone_active_over_idle` columns of
  memtile_power.csv; `*-synopsys-ptpx-synth-*-power/outputs/power.*` zipped.
  Needs lake >= `6a79216c` on the host `--lake-dir`: before it, those leaves
  powered RTL-sim activity (~2–4% of nets annotated, idle ≈ active). For a
  standalone workspace built earlier, `make clean-<N>` its
  `synopsys-vcs-sim-{idle,active}-power` steps.
- Not covered: app-driven power (application/testbench/post-pnr-power need an
  app bundle for spec tiles), RV mode, debug-calibre. Build machine needs the
  standalone garnet AND its sibling lake pulled (the standalone flow uses the
  host lake; lake ≥ 577c6beb for the shared power programs).
- **Result (zip `STANDALONE_r8cad-gf12_20261007-224116`, 2026-10-07):** RTL at
  lake 577c6beb, hierarchy kept (`port_sg_0`/`port_ag_0`/`memoryport_0_storage_0`
  rows in the tile area report), synth meets 1.333 ns (tile +0.2 ps, standalone
  +1.6 ps), SRAM period PASS, fix-tap-gaps moved 34 taps, Innovus signoff WNS
  −90 ps (In2Out), tile memtile power 100% SAIF-annotated at synth and PnR
  (idle 1.59 / active 10.5 mW synth, 2.04 / 11.6 mW PnR). Not valid: PT signoff
  + genlibdb (truncated SDC, fixed by fix-pt-sdc.tcl above); standalone power
  (simulated the RTL — run predates lake 6a79216c — 50.8% nets / 0.29% cells
  annotated, active/idle 1.49 vs the tile's 6.6). `--also-make` DRC/LVS/DRC+
  failed on setup, not on the design: `inputs/adk/run-drc-pm.csh` missing,
  `GF_PDK_HOME` unset (`drcenv-block.sh`), Calibre `ixl_cal_2013.2` too old for
  the LVS deck (`device::enclosure_parallel_measurements`); lib2db never started
  (make stops after the first failure). Innovus's own `verify_drc` caps at 1000
  (≈980 C5/K1 shorts + M3 EOL spacing) and `verifyConnectivity` finds 9 VSS
  opens on every PnR build so far (also the 2026-10-06 thesis anchors) — a
  flow-wide power-grid issue, fine for PPA but not DRC-clean.
  Signoff timing (Innovus `signoff.summary`): WNS −0.090 / TNS −1.948 ns,
  227 violating paths, all IO-facing (In2Out −90 ps ×91, In2Reg −33 ×76,
  CriticalPassThrough −11 ×58, Reg2Out −9 ×2); Reg2Reg −0.000, hold met
  (+9 ps), synth met by only +0.2 ps. DRVs: 1 max_tran (−9 ps), 1 max_fanout.
  Antenna 0, SI glitches 0, density 70.5%. Genus log clean (only the
  intended `mode[0]` probe SDC-208 ×2 and 2 unused decoder regs).
  **The three MMMC views (UNIFIED_BUFFER / FIFO / SRAM) are identical on a
  spec MemCore**: constraints.tcl skips the per-mode case analysis (no
  `mode[0]` pin), so PnR times the same constraints 3× -- dropping to one
  view would save PnR runtime, not change results.
- Checked on /aha (stub ADK): dry-run sequence; both graphs materialize, every
  target name resolves/exists, tile build reaches gen_rtl (no docker here),
  standalone reaches lake gen_sram (no SRAM compiler); make-sequencing + notes
  + done.flag on a scratch graph; standalone power columns on synthetic reports.

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
`*.timing.setup.rpt`; PT prints gf12 times in ps, converted to ns from the
report's clock edges since 2026-10-07 — earlier CSVs hold ps). Parsers are
fail-soft (blank cell). Validated against
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
  `--stop-after`. **For lake-spec configs pass `--app-bundle-dir`** (see "App
  bundles" below): without a bundle the `application` step runs the app on the
  *default* MemCore in the stock `stanfordaha/garnet:latest` container (no spec
  flags, upstream aha/clockwork, 2020-era VCD/place paths), so the stimulus
  replayed into the spec tile is wrong and the power numbers are meaningless
  (the sweep warns per config). Plain PnR sweeps (no power flag)
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
- **`Tile_MemCore/custom-init/outputs/fix-tap-gaps.tcl`** — lake-spec builds
  only (`construct.py` adds it to custom-init's outputs and to init's `order`
  right after the endcap/well-tap script; the default onyx graph is
  unchanged). GF12's smallest filler is 2 sites and taps/endcaps are fixed,
  so a well tap that lands exactly one site from a fixed neighbor leaves a
  hole nothing can fill or move → `SPFillerGapViolation` → route's
  `routeDesign -placementCheck` aborts with NRIG-76. It depends on where a
  macro halo edge falls against the tap grid (i.e. die width): static
  `fw4_dw16_sc8192_dp_in4_out4_vc2` hit it in 116 rows (TAPX14 one site short
  of the ROWCAPRX8 beside the second SRAM), its wider `_rv` twin didn't. The
  script measures each tap's clearance to fixed cells directly (not via
  checkPlace, whose filler-gap check needs the place step's
  `place_detail_legalization_inst_gap`) and moves offenders one site, widening
  the gap to 2 (or abutting if widening would leave a new 1-site gap). Init
  log prints `INFO: fix-tap-gaps: N well taps had a 1-site gap ...`. Verified
  on that config's re-run (zip `..._20261006-221414`): 116 found, 116 moved,
  CTS checkPlace clean, route → signoff passed.
  Superseded a 2026-10-06 route-step `setFillerMode -fitGap true` hook that
  changed nothing (fitGap only moves placed cells, not fixed ones). Every
  route log also shows the second "addFiller without DRC checking" pass
  placing DRC-violating `FILL_incr` cells — those route fine but are a latent
  signoff-DRC issue.
- **`Tile_MemCore/custom-signoff/outputs/fix-pt-sdc.tcl`** (2026-10-07) —
  lake-spec builds only (new `custom-signoff` step feeding signoff; sourced
  right after `generate-results.tcl`). `writeTimingCon` splits long object lists
  into `set __coll_N [get_ports {...}]` + `append_to_collection __coll_N [...]`,
  and `append_to_collection` isn't SDC: PrimeTime's `read_sdc` stops at the
  first one (CMD-005 / "Errors reading SDC file") and silently drops the rest.
  All four readers of `design.pt.sdc` hit it (PT signoff, genlibdb, PnR-level
  memtile power idle/active); synth-level power reads Genus's SDC and was fine.
  On the 2026-10-07 smoke run reading stopped at line 4283, and the lost
  constraints included the 2-cycle `config_config_addr -> read_config_data`
  multicycle, so PT reported −1229 ps on that path vs Innovus's −90 ps. The
  script folds each collection's appends into its `set` line (same `get_*`,
  not referenced in between; else left and counted), keeps
  `<design>.pt.sdc.orig`, and logs `INFO: fix-pt-sdc: folded N ...; M left`.
  PT signoff and genlibdb (lake-spec) also get the postcondition
  `'Errors reading SDC' not in File( 'mflowgen-run.log' )`. Checked locally on
  the real SDC lines PT echoed (442-port collection preserved) + edge cases,
  and both graphs materialize; not yet run through PT. Workspaces whose signoff
  already ran need it re-run (`--clean-stale` sees the new signoff `order`).

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

**Local generic power, end to end (2026-10-06, freepdk45, SRAM as flops,
100 MHz, DC netlist, gate-level sim, PT; 100% nets annotated).** Idle / active
total mW:

| spec | standalone `lakespec` | Tile_MemCore |
|---|---|---|
| fw1 DP 1×1 1 KB | 5.31 / 7.86 | 9.47 / 12.8 |
| fw2 SP 1×1 2 KB | 9.39 / 17.8 | 15.7 / 30.7 |
| fw4 SP 2×2 4 KB | 18.9 / 33.4 | 30.0 / 60.3 |
| fw4 SP 2×2 4 KB RV | — (no standalone RV) | 30.1 / 76.6 |
| fw4 SP 2×2 4 KB dw8 | 18.8 / 27.8 | — |

The storage flops are the largest share (54–95%), and SB + CB are ~1.3 mW. Every
sim printed its PASS line, and memtile_power.csv parsed the real PT reports.
Four things to know when reading synth-level numbers:
- **The tile pays ~4 mW of clock that the standalone design doesn't, at
  synth level only.** MemoryTileBuilder gates the core clock in logic
  (`NOR2(mode, ~clk)` → lakespec, `INV` → SRAM/FIFOs). Before CTS, those
  gates each drive thousands of flop clock pins, and PT books their nets as
  `clock_network` switching: 3.9 mW at fw2 2 KB, the same in idle and active.
  The standalone clock comes straight from a port and is ideal (≈0). This is
  most of the tile's higher idle number, so compare standalone vs tile on
  `report_power` groups or at the PnR level (real clock tree).
- **The NanGate freepdk `DFFR_X1` model needs `+define+TETRAMAX` in gate
  sims.** Without it, the model's `ng_xbuf` drives its own RN pin, so async
  reset goes X and the RV tile fails. Seen with freepdk; the gf12 cell
  models were not checked (no gf12 ADK on /aha).
- **Don't apply an RTL-sim SAIF to a gate netlist without a name map.** PT
  matched only ~2–4% of nets that way, and idle came out ≈ active; a sim of
  the netlist itself gives 100%. Lake `pd/thesis` synth-level idle/active
  power did this until lake `6a79216c` (2026-10-07), which simulates the
  Genus netlist. The tile flow always simulated the netlist.
- **Use DC `analyze`+`elaborate` on garnet.v.** `read_file` black-boxes the
  parameterized coreir templates (LBR-1).

## Helper scripts (build machine can't run Claude)

- **`watch_step.sh`** — follow the active mflowgen step live (auto-hops as
  steps advance; maintains a `current-step.log` symlink). `--symlink-only`,
  `--list`. `--summary <out-dir>` (2026-10-06): whole-sweep status — done /
  running (step, time in step, log-quiet time, last log line; flags a
  Genus/Innovus/PT prompt = tool stopped on an error, with the pid to kill) /
  failed-stopped (step it died in) / not started, plus whether sweep_specs.py
  is alive and a verdict line. Running = a live `make`/`mflowgen` whose cwd is
  the workspace (/proc scan); `.time_start` without `.time_end` alone can't
  tell running from died (step scripts are `set -e`; `--list` now checks
  processes too). Not-started needs `<out-dir>/sweep_plan.txt` (written by
  sweep_specs at each run start: `# pid= host= started=` + command + one
  `workspace targets` line per config); for a run that predates it,
  `sweep_specs.py <same selection flags> --list > <out-dir>/sweep_plan.txt`
  Without a plan pid header it finds the sweep by matching a running
  `python … sweep_specs.py`'s `--out-dir` (resolved against its cwd). While
  the sweep zips, it shows the `.zip.partial` size and the file being
  compressed (from the sweep's `/proc/<pid>/fd`). For a RUNNING config with
  no unfinished step it shows what `make` still waits on (its child
  processes) and, for a step `tee`, every other process holding that step's
  output pipe (found via `/proc/*/fd`, so daemons that `cd /` are caught),
  with the pid to kill. Tested on a fake sweep tree, a real `make` running
  mflowgen's `./mflowgen-run 2>&1 | tee` recipe with a stray daemon holding
  the pipe (killing it let make finish), and a stub-ADK sweep on /aha (bash 5).
- **"Last step done but the sweep never moves on":** mflowgen runs each step as
  `./mflowgen-run 2>&1 | tee mflowgen-run.log`, and make only continues once
  that `tee` sees EOF, i.e. once EVERY process holding the pipe exits. A step
  can finish (`.time_end` written, outputs there) while a background child it
  started keeps the pipe open: make, and sweep_specs, then wait forever and
  that config never prints PASS. After all configs pass, `--zip` is the last
  long phase (now with progress lines, see `--zip` above).
- **Why a sweep looks hung:** sweep_specs prints a config's PASS/FAIL only
  when its whole build ends, and waits for every config (both `--pnr-set`
  pools) before `Done:` + correlation + zip. With `--pnr-set full12
  --pnr-jobs 2` the synth pool finishes long before the 12 PnR builds, so
  hours of silence is normal. Tool-prompt hangs are fixed by stdin=/dev/null
  (Key flags above; reproduced with Genus 20.11 here): at EOF Genus exits
  **0**, so it's the node postconditions (Genus `outputs/design.v`, Innovus
  `outputs/design.checkpoint`) that fail the step. The stock PT signoff node
  has none, so Tile_MemCore / tile_array / full_chip add
  `assert File( 'outputs/design.sdf' )` (pt.tcl's last write; a dangling
  outputs/ link fails `File`). The `--memtile-power` ptpx steps are covered by
  their own `cp reports/*.power.{hier,cell}.rpt` under `set -e`.
- `done.flag` = the latest build of that workspace passed: sweep_specs deletes
  it when it starts rebuilding a workspace (so a failed re-run never reads as
  done).
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

### App bundles: real-app power on lake-spec tiles (2026-10-06)

The stock `application` step runs the app in `stanfordaha/garnet:latest` on
the DEFAULT MemCore, so for a lake-spec tile its stimulus is wrong. Fix
(user decision, option A): record the app run where the spec toolchain lives
(/aha: lake-spec garnet + spec collateral in clockwork + the static/RV
recipe, memory `reference_spec_cgra_app_sim`) as an **app bundle**, and
replay it here.

A bundle is one directory per (spec, mode, app): `run.vcd` (every placed MEM
and PE tile's ports, `-depth 1 -ports` probes, from a bit-accurate `aha test`
run on the spec CGRA), `tiles_Tile_{MemCore,PE}.list`, `tile_ports.json`
(each tile module's ports from that garnet.v) and `manifest.json` (app, mode,
spec, scope `top.dut.Interconnect_inst0`, clock `{scope}.{tile}.clk`,
garnet.v md5, toolchain versions).

- `common/application`: param `app_bundle` (Tile_* construct: env
  `APP_BUNDLE`) → copies the five files instead of running the container;
  `check_bundle.py` fails the step unless the bundle's spec + mode equal this
  build's `lake_spec_config` / `lake_spec_mode` (`app_bundle_check`, off for
  Tile_PE; missing spec keys take lake `build_spec`'s defaults, so a bundle
  spec without `vec_capacity` matches a sweep `_vc2` config). Without a
  bundle it writes `{}` for the two JSON outputs.
- `common/testbench/generate_testbench.py`: scope, sampling clock and the
  per-design port lists come from the bundle (17-bit SB buses + valid/ready,
  flush, config pass-through ...); clock inputs (`clk`, `clk_pass_through`) are
  driven by the tb clock, clock outputs are not compared. `{}` inputs → the
  old `Interconnect_tb` scope + `defines.py` lists (legacy path unchanged).
  `$sdf_annotate` is skipped under `+define+NO_SDF` (RTL replay). The step
  needs Xcelium's `simvisdbutil` on PATH (`module load xcelium`); its run.sh
  now has `set -e` (before 2026-10-07 a generator crash still "passed" the
  step with no testbench.sv).
- `sweep_specs.py --app-bundle-dir DIR`: config `<name>` uses `DIR/<name>/`
  (the sweep's config name, e.g. `fw4_dw16_sc8192_sp_in2_out2_vc2` or
  `..._vc2_rv`; `_tile_env` sets `APP_BUNDLE`); `--cgra-power` without one
  warns that the config's power comes from the default MemCore.

Validated on /aha: static conv_3_3 on spec `fw4_dw16_sc8192_sp_in2_out2`
(16x16): bundle sim bit-accurate; per-tile replay of all 12 placed tiles
(2 MEM, 10 PE) on the tile RTL from the same garnet.v = 0 output mismatches
over 7539 cycles (xrun with `-initmem0 -initreg0 -xminitialize 0`, as
`aha test` uses, and the ChipWare `CW_fp_*` models for Tile_PE; without the
init flags one MEM tile's unused output is X). The application + testbench
step scripts were run with a bundle as mflowgen would run them. NOT run here:
the gf12 netlists / ptpx steps (no ADK). (`cadence-xcelium-sim` now
zero-initializes like `aha test`; see "Local app-driven power".)

**Making bundles: `common/application/gen_app_bundle.py`** (run in /aha, not
on the build machine; needs xrun on PATH and aha's venv):

    python3 mflowgen/common/application/gen_app_bundle.py \
        --config fw4_dw16_sc4096_sp_in2_out2_vc2_rv --app tests/conv_3_3 \
        --bundle-dir <dir> [--aha-dir <private aha tree>] [--pond-spec pond.json]

`--config` takes a sweep_specs config name (spec + mode as the sweep writes
them; the bundle lands in `<dir>/<config>`, the layout `--app-bundle-dir`
reads). Steps: collateral → `aha halide/map --collateral` → `garnet.py
--verilog` (spec flags, `--use_sim_sram`, 16x16 default) → `aha pnr` → `aha
test` with `DUMP_ARGS=-input probe.tcl` (tests/test_app/Makefile now takes
`DUMP_ARGS` from the env), which must print `comparison passed`; RV runs get
aha's per-stage ready-valid env. `--skip-to` resumes. Extra outputs beside the
five the application step copies: `core.vcd` + `core_ports.json` (each MEM
tile's lake controller, `lakespec_mem_flat`, at its ports: config_memory,
port data/valid/ready, flush — the standalone-lakespec replay input),
`garnet.v.gz`, `design.place`, the bitstream, `logs/`. `garnet.py --verilog`
rewrites the GLB/GLC headers of `$GARNET_HOME`, so on a shared /aha use a
private aha tree (`--aha-dir`, run through `aha --dir`).

**Per-tile power sub-graphs ADK (fixed 2026-10-07):**
`common/tile-post-{rtl,synth,pnr}-power/construct.py` hard-coded
`adk_name = 'tsmc16'`. Without a tsmc16 ADK the per-tile `mflowgen run` died
("Could not find adk tsmc16"); with one it silently powered gf12 netlists with
tsmc16 libraries. They now take the parent graph's `adk`/`adk_view` (new
params of the three steps, exported by mflowgen; fallback `get_sys_adk()`).

**RTL power level (`tile-post-rtl-power`) never produced a report; fixed
2026-10-07.** Found by running the sub-graph locally:
- its RTL sim compiled the signoff netlist too (`cadence-xcelium-sim` takes
  every `inputs/*.v`; by-name edges handed it `design.vcs.v`), and the
  netlist's tile module replaced the RTL one (`-ALLOWREDEFINITION`). Now
  explicit edges: design.v, testbench.sv, cmd.tcl, test vectors (+ sram.v).
- `cmd.tcl` (the SAIF window) was not passed → no run.saif. Now an input of
  the step and its setup.
- Tile_PE's RTL needs ChipWare `CW_fp_*` sim models: `run_sim.sh` adds `-y
  $CW_SIM_DIR` (default: next to `genus` on PATH,
  `<genus>/share/synth/lib/chipware/sim/verilog/CW`); harmless for netlists.
- Genus `write_name_mapping` (= `design.namemap`) is Conformal LEC syntax
  (`add mapped point <rtl>/q <inst>/Q -type DFF DFF`), which PT cannot
  `source`. `synopsys-ptpx-rtl/namemap_to_pt.py` turns it into
  `set_rtl_to_gate_name` per register (Q pin's net; QN and ports skipped).
- Tile_MemCore wired `synth` into `post-rtl-power` by name, so `design.v` had
  two sources (rtl + Genus netlist; the last link wins). Now only
  `design.namemap` comes from synth. (Tile_PE has no RTL-level node.) Still
  ambiguous, untouched: `post-pnr-power`'s `design.sdf` comes from both
  `cadence-innovus-signoff` and `synopsys-pt-timing-signoff` (since 2022).
Local result (Tile_PE, freepdk45): every register's Q net annotated from the
RTL SAIF (50% of sequential nets = all Q; QN implied); totals equal the
synth level (PE 2.66 / 3.08 mW; MEM 34.8 / 31.9 vs synth 34.8 / 32.9).

**Local app-driven power, end to end (2026-10-07, /aha, freepdk45 at
100 MHz, `--use_sim_sram` SRAM as flops).** Bundle
`fw4_dw16_sc4096_sp_in2_out2_vc2` (static conv_3_3, 16x16) from
`gen_app_bundle.py`; RV twin `..._rv` likewise. Every tile of both bundles
replays bit-exactly at RTL (12 + 11 tiles). Tile netlists from Genus with
mflowgen's naming styles; then the real step scripts on a local freepdk45 ADK
(scratchpad `localadk/`, a `view-local` with a compiled `stdcells.db`):
`common/testbench` (bundle mode) → `tile-post-synth-power/run_all_tiles.py`
→ per tile `cadence-xcelium-sim` + `synopsys-ptpx-synth`; 100% of nets
annotated. Results (with both fixes below): Tile_PE 2.7–3.5 mW per placed PE
(1.8–2.2 mW internal; switching 0.09–0.58 mW tracks the PE's activity);
Tile_MemCore 34.8 mW (stencil-valid tile) / 32.9 mW (conv line buffer).
(Hand-run Genus here: its default SDC needs the compat read; mflowgen's own
genus step writes a strict SDC.)
- **Zero-init (fixed 2026-10-07):** `cadence-xcelium-sim` ran with no X
  initialization, while `aha test` (which records the bundle) uses
  `-xminitialize 0`. The MEM tile's SRAM (flops under `--use_sim_sram`) then
  stayed X: the line buffer's warm-up taps came out X for 1200 cycles, and PT
  booked the X-state flops at 1.5–3.8 W per tile. `run_sim.sh` now passes
  `-xminitialize 0 -delay_udp_xminitialize` (the second reaches the stdcell
  flops' UDP state; `-initreg0`/`-initmem0` and time-0 `deposit`s on the UDP
  output do not). Replays then match on every cycle (no X at cycles 0–1
  either). With gf12 SRAM macros the array is not flops, but the macro
  model's warm-up reads are the same story.
- **ptpx steps read the SDC through `read_sdc_compat.tcl` (2026-10-08).**
  PrimeTime's `read_sdc` stops at the first non-SDC line and drops the rest.
  Genus's DEFAULT SDC has `current_design <top>` at line 13, so a flow that
  reads it runs power with NO clock: lake's standalone ptpx (fixed in lake
  33eae24e) and my local freepdk45 harness, which used `write_sdc` output
  (symptom: the gated SRAM clock became a data net, 72 ns CK slew, 4.4 W per
  MEM tile; I first misread that as a pre-CTS artifact). **The mflowgen
  Tile_MemCore / Tile_PE synth level was NOT affected:**
  `custom-genus-scripts/copy_sdc.tcl` makes synth's `design.sdc` the
  `write_sdc -strict` output, which has no `current_design`. The 2026-10-07
  gf12 smoke run's `memtile-power-synth-*` read the whole SDC (clock 1333,
  100% annotated). So in garnet 6ac4d73f (copies of lake's file in
  `synopsys-ptpx-{synth,gl,rtl}/`, each step failing on "Errors reading
  SDC"), the compat read is a no-op for those steps and the guard is the
  value. Its commit message ("synth-level tile power had no clock") overstates
  it: that applied to the local harness only. With a clocked SDC, the local
  MEM tiles' synth level gives 34.8 / 32.9 mW, matching the RTL level
  (34.8 / 31.9); `clock_network` ≈ 86%.
- Gotcha: a Genus netlist WITHOUT mflowgen's `hdl_array_naming_style %s_%d`
  (and bus/uniquify styles) has escaped array nets (`\x[20] [16]`) that
  Xcelium's SAIF spells in a way PT's `read_saif` rejects ("syntax error",
  0% annotated, power = defaults). mflowgen's genus step sets them; any
  hand-run synthesis must too.
- Standalone (lake `app-power-gen`, see lake CLAUDE.md §2): conv_3_3's line
  buffer tile replayed into the standalone lakespec reproduces the tile's
  lakespec outputs in value and cycle; idle 18.9 / app 30.5 / active
  33.4 mW. `sweep_specs --standalone-synth --app-bundle-dir` passes the
  bundle (static configs) as graph kwarg `app_bundle` and makes
  `synopsys-ptpx-synth-app-power`.
- `memtile_power.csv` gains `standalone_app` (app:tile),
  `standalone_app_{internal,switching,leakage,total}_power`,
  `standalone_app_over_idle`, `tile_app` and
  `tile_{rtl,synth,pnr}_app_total_power` (that MEM tile's
  `*-post-<level>-power/outputs/reports/<tile>.hier`).

The dormant `--per-tile` flag (`common/tile-per-tile-power`, untracked since
2026-09-27, never wired into the graph) was an earlier attempt that powers only
the lake memory core in isolation; bundles cover the whole tile (interconnect +
config) for MEM and PE tiles at all three power levels.

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

aha's `mek` branch tracks the tips of garnet `modern_gf` and lake `THESIS`:
after pushing either, bump its gitlink on `mek` (`git update-index --cacheinfo
160000,<sha>,garnet` (or `lake`), commit `Bump garnet: <what>`, push). Other
sessions bump it too, so first `git fetch` both repos, fast-forward `mek`, and
only bump when `git merge-base --is-ancestor <current gitlink> <new sha>`
holds (gate the update on it with `&&`); otherwise set it to the branch tip.
2026-10-07: 8840857 skipped that check and moved garnet back a commit
(fixed in 294a61b).
