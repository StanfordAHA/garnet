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
- `--spec-set {default,thesis,filter_fifo,clock_gating}` — `default` = the 6 `DEFAULT_SPEC_POINTS`;
  `filter_fifo` = the conv_3_3 A/B spec (RV, `_ff8`; see "Whole-CGRA power of
  app variants"); `clock_gating` = the clock-gating A/B (below);
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
- `--clock-mhz MHZ` (2026-10-11) sets the tile clock as env `CLOCK_PERIOD`
  (ns = 1000/MHZ, rounded to 1 ps); Tile_MemCore construct.py
  `clock_period`, default 1.333.
  - Through `update_params` it reaches constraints (the clock-scaled IO
    budgets: i_delay 0.2T, o_delay 0.1T, SB in→out max_delay T), synth,
    gen_sram's period check, and the power test-gen / sim (`CLK_PERIOD`).
    Innovus and PT take it from the synth SDC. Verified by materializing the
    graph at 900 MHz: every clocked step gets `clock_period=1.111`.
  - The standalone synth follows (1111 ps) unless `--standalone-clock-ps`.
  - Exported only when it differs from the graph default, so `--clock-mhz
    750` on an old 1.333 ns sweep is a no-op, not a "changed settings"
    rebuild.
  - A different clock re-materializes the graph, and the stale-step check
    then fails or (`--clean-stale`) re-runs every clocked step. Give each
    clock its own `--out-dir`.
  - correlation.csv / memtile_power.csv gain `clock_period_ns` and
    `clock_mhz`. Read from the manifest, else the synth step's parameter,
    else the Genus top-100 capture edge, so old zips read 1.333 / 750.2.
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
graph materialization. Genus SRAM area (.lib `area`) and Innovus macro area
(LEF footprint) differ: 5769.8 vs 5624.9 (0.975) on the 2026-10-07 smoke run.
Since 2026-10-08 via_logic scales the synth SRAM area by the fit configs'
PnR/synth macro ratio (`_sram_macro_ratios`: same macros if any fit config
has them, else the fit mean, else 1.0; per-row `tile_sram_pnr_over_synth_used`).
Synthetic check with 0.970-0.980 ratios: held-out error 0.35% vs 0.76%
uncalibrated, and no longer all-positive.

**Result (zip `NEW_SWEEP_r8cad-gf12_20261009-213941_slim`, 2026-10-09):** all
172 PASS (power sims, 100% SAIF annotation, SDC read, SRAM period all clean;
fix-pt-sdc folded 46–65 lines per PnR tile, 0 left). The zip's CSVs are the
corrected ones (reproduce byte-for-byte with `--correlate-only` at cbfac590).
Held-out error: total area 0.38% mean / 0.81% max, logic 1.01 / 1.61%, idle and
active power ~3 / 6%. Leave-one-out over all 12 PnR builds agrees: per-mode
direct total-area fit ≤0.83% (the via-logic estimate doesn't beat it), power
≤6.3% active / ≤7.5% static idle; the pooled fit is much worse for power (11.8%).
**Tile RTL was generated at 8 lake commits** (gen_rtl takes `origin/THESIS` at
RTL time and the sweep spanned two days). The only RTL-changing one is
`8748240d` (RV comparison-network wrap fix, dims 2/4/8): all 9 dims-2 RV configs
and 5 of 9 dims-4 RV configs predate it (+6% comparison network, +0.84% tile
area on the measured dims-4 pair, power identical), including held-out
`..._dim4_msw1024_rv`. garnet RTL generation is the same across the two garnet
commits used (fb50802c, ecb52e48). Ingested per block by lake
`THESIS/pipeline/tile_sweep.py` (lake CLAUDE.md §1.8).
**Earlier review (cfc4174c, first zip `NEW_SWEEP_r8cad-gf12_20261009-132919`, 2026-10-09):**
all 172 PASS (96 built, 76 `already_done` from the 2026-10-07 launch); every
manifest has FLATTEN 0 / MEMTILE_POWER / non-split FIFOs; 368 power sims PASS,
368 PT power runs 100% annotated with no SDC errors; SRAM period PASS; Genus
met timing everywhere (WNS ≥ 0) with no errors or black boxes. Garnet
was pulled mid-run, so step scripts are mixed: 101 synths have 3 timing modes,
71 have 1 (d79bf443). The same config synthesized both ways differs by 0.18%
in logic area with identical power, so mixing them doesn't matter. The
sweep's Python dates from between 505c1e8c and 546b1e46, so its CSVs lacked
the SRAM calibration, and the PT unit check misread two RV tiles whose top
100 are all in2out `max_delay` paths (-11.968 ps as -11.968 ns; fixed in
2519107d). Rerun `--correlate-only` with the same args (seconds, no rebuild)
after pulling garnet. Regenerated: held-out |err| total area 0.38% (max
0.81%), via_logic 0.61% (was 1.10%; max 0.82%), logic 1.01%, idle power
3.11% (max 5.97%), active 3.09% (max 5.85%); fw4_dp_4x4_rv is extrapolated
(total area, active power). PnR timing: PT PBA WNS -6 to -49 ps, mostly in2out
feed-throughs (config bus, flush, SB ready→valid; `max_delay` 699.9 ps). PBA
reg2reg misses only on 4 tiles (-0.9/-1.1/-9.2/-17.4 ps; GBA -3 to -40 on 9
of 12). The -24.6 / -14.0 are in2reg (`stall`/`flush` → SB FIFO); I first
miscounted them as reg2reg, because PT prints short port names' "(input
port)" on the name's line. Critical paths (2026-10-11, full #1-path reports):
- **Synth, static tiles (89):** `flush` → flush mux → schedule-gen /
  iteration / address counters. `flush` is a pass-through input with a
  *fixed* `pt_i_delay` 0.700 ns (constraints/common.tcl), so about 0.6 ns of
  logic (20–32 stages) is left at 1.333 ns.
- **Synth, RV tiles (83):** a full-cycle internal path (about 1.3 ns, 36–74
  stages) through the RV controller: config reg or iteration counter →
  `rv_comp_network`/`lfcompblock` (dependence check) → `port_sg` step →
  arbiter → `port_id` → `port_ag` update. It is real logic: 6 configs start
  it at an iteration counter, so relaxing config-register paths wouldn't
  help.
- **PnR, SB `ready`→`valid`:** the SB feed-through budget is a fixed
  `sb_delay` 0.3 ns plus i/o delays, and the miss grows with tile size
  (Spearman −0.89: −2 ps at 10k µm², −49 ps at 50k µm²).
- **PnR, pass-through `*_out`:** about 80 ps in-tile window
  (clock_max_delay 0.05 + margin 0.03); misses −6 to −19 ps.
- **PnR, reg→reg:** only the RV-controller path, at most −17.4 ps.
- **At 900 MHz:** the fixed budgets don't move, the static flush path loses
  222 of its ~600 ps, and the RV path must shrink ~15%.
PT hold violations on 3 tiles are only the clk→clk_out
feed-through (-0.5 to -16.5 ps). Innovus: verify_drc 1000 everywhere (the
edge-blockage artifact, see smoke run); VSS opens 9 on sp tiles, but 109/110 on
fw2 dp 2×2 and 214 on fw4 dp 4×4 RV.
Extracted (minus GDS) with the regenerated CSVs and an analysis handoff at
`/aha/sweep_out/dw16_NEW_SWEEP_20261009/` (`HANDOFF.md`; build-machine CSVs in
`csv_as_zipped/`).

### Clock-gating A/B through PnR (2026-10-14, session 5b33d095)

Lake 9f9480c9 adds two opt-in Spec power options, both off by default:
- `share_clk_ctr`: one cycle counter for every static schedule generator,
  instead of a 34–39-bit `clk_ctr` in each (8 in a fw4 2×2 static spec,
  292 flops, about 35% of that gf12 tile's idle power).
- `clock_gate_ports`: each port's logic on a clock gated off while the app
  leaves the port unconfigured.

Details are in lake CLAUDE.md §5.6. `--spec-set clock_gating`
(`CLOCK_GATING_SPEC_POINTS`) builds the default onyx geometry (fw4 4 KB 2×2,
vc2) six ways, with modes pinned. Name suffixes are `_sharectr` / `_portcg`:
- static: base, `_sharectr`, `_portcg`, `_sharectr_portcg`;
- RV: base and `_portcg`. `share_clk_ctr` is refused for RV, since RV specs
  have no free-running schedule generators.

The two keys reach garnet as `spec_config.json` → lake
`build_spec`/`build_spec_rv` kwargs. The power-test generator rebuilds the
same spec, so its bitstreams carry each configured port's `port_enable`. The
idle program configures no port, so a gated tile's ports are clocked off in
idle. Build-machine command (garnet with this section; lake >= 9f9480c9 at
origin/THESIS, which gen_rtl and the test generator check out in the container):

    ./mflowgen/sweep_specs.py --spec-set clock_gating --flatten-effort 0 \
        --memtile-power --config-jobs 6 --zip \
        --out-dir /nsim/mstrange/BUILDS/sweep_out/clock_gating_ab

All six run to PT signoff, plus synth- and PnR-level idle/active power.
`--flatten-effort 0` keeps the hierarchy for per-block power: port logic vs the
rest, as in the dw16 sweep. The base static config has the same name as the
thesis set's `fw4_dw16_sc4096_sp_in2_out2_vc2`. A fresh out-dir builds all six
at one lake commit.

Checked on /aha before the push:
- Flags off: byte-identical RTL from `build_spec` / `build_spec_rv`.
- Tile RTL of four variants (gen_rtl flags + `--use_sim_sram`): static base,
  `_sharectr`, `_sharectr_portcg` and RV `_portcg`. memtile-power-test-gen,
  then memtile-power-sim idle + active: all PASS. Static outputs change
  981/980 times in 1000 cycles in every variant; RV 976/975.
- SAIF of the gated tiles: every `port_<i>_gclk` has TC 0 in idle, and
  `shared_clk_ctr` stops too (it is enabled only while some port is
  configured). In active, configured ports toggle 1999 and the counter counts.
  The RV filter port stays gated in active, since the program doesn't use it.

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
  opens on every PnR build so far (also the 2026-10-06 thesis anchors). The
  DRC count is an edge-blockage artifact; the VSS opens are real (triage
  below).
  Signoff timing (Innovus `signoff.summary`): WNS −0.090 / TNS −1.948 ns,
  227 violating paths, all IO-facing (In2Out −90 ps ×91, In2Reg −33 ×76,
  CriticalPassThrough −11 ×58, Reg2Out −9 ×2); Reg2Reg −0.000, hold met
  (+9 ps), synth met by only +0.2 ps. DRVs: 1 max_tran (−9 ps), 1 max_fanout.
  Antenna 0, SI glitches 0, density 70.5%. Genus log clean (only the
  intended `mode[0]` probe SDC-208 ×2 and 2 unused decoder regs).
  The three MMMC views (UNIFIED_BUFFER / FIFO / SRAM) were identical on a
  spec MemCore (no `mode[0]` pin, so no per-mode case analysis); spec builds
  use one mode since 2026-10-08 (constraints.tcl bullet below). IO-path
  slack stays as is (user decision 2026-10-08): it is recorded per config in
  correlation.csv (`tile_synth_wns_ps`, PT `tile_pnr_setup_wns_ns`,
  `tile_pnr_innovus_wns_{all,reg2reg,in2reg,reg2out,in2out}_ns`).
  DRC triage (2026-10-08, from `Tile_MemCore.geom.rpt` of the 21:53 re-zip;
  the verify_drc report is `<design>.geom.rpt`, zipped since 546b1e46 with
  `.conn.rpt`/`.antenna.rpt`): all 1000 listed violations are wires vs
  **Routing Blockage**, not metal vs metal. 984 are tile pin stubs inside
  common/init-scripts/edge-blockages.tcl's 0.18 µm all-layer edge blockage
  (C5 on top 321 / bottom 189, K1 on left 255 / right 219; the blockage is
  made after pin assignment and pins must cross it by design); 16 are M3
  EndOfLine spacing to a blockage in the interior (likely the SRAM M3
  `-pgnetonly` halo in custom-init/floorplan.tcl). Routing blockages aren't
  in the GDS, and NanoRoute ends at 0 DRC in route/postroute/postroute_hold,
  so no real routing DRC is known; but verify_drc stops at its default
  `-limit 1000`, so anything past the artifacts is hidden (Innovus 22/23 has
  no "ignore routing blockage" option; raise `set_verify_drc_mode -limit`).
  Antenna: none. VSS opens (`.conn.rpt`): 1 special-wire open spanning the
  die + 8 regular-routing VSS pieces: full-width bands just inside the
  bottom/top edges (y 0.45–0.69, 108.69–108.93; x 1.5–197.3), bands along
  the SRAM columns' edges (x 50.5–91.3 and 107.7–148.5 at y 20.4–20.6 and
  89.7–90.0), and short pieces beside them (y 27.1–27.3 at x 48.3–49.8 and
  149.4–150.6).
  **Root causes (pg_diag run 2026-10-10 on the smoke tile + fw2 dp 2×2 + fw4
  dp 4×4 RV; reports in cfc4174c's scratchpad `pgd/`):** no logic cell sits
  on any open. Two kinds:
  - **Column caps.** Every non-stripe open is a row of
    `SC7P5T_NOM1COLCAPNX3_SSC14R` cells (physical-only, from the gf12 ADK's
    `adk_add_end_caps`, 3276 per tile) at a row-region edge: core top/bottom
    (777 each), the rows above/below each SRAM (162), and a few beside them.
    These are sp opens 2–9, plus 6 per dp tile. The M1 VSS followpin beside
    them is connected (152 V1 vias). What stays open is the caps' **VPW well
    pin**. The ADK's `setEndCapMode` puts the bottom-edge cap NX3 on both
    `-topEdge` and `-bottomEdge`. NX3's PG pins (pg_diag v2 `cells.txt`) are
    VSS on M1, VPW on `SXCUT` (lower 0.24 µm), and VNW on NW; it has no VDD
    pin. `globalnetconnect.tcl` ties VPW to VSS, but a well shape reaches
    VSS only through a well tap. Cap rows hold no taps, and the cap's VPW
    faces outward (to the core edge or the SRAM), so each cap row is an
    isolated VSS piece. The open boxes match the VPW rects exactly (e.g.
    0.448–0.688, 108.688–108.928).
    These are not metal and touch no devices: an abstract-level artifact of
    the ADK's edge caps, the same on every gf12 tile (full chip too). No
    flow change:
    - tapping cap rows (`setEndCapMode -boundary_tap true`) changes cell
      count and area mid-sweep;
    - untying cap VPW from VSS would make the LVS netlist wrong.

    pg_diag (b7ebb5c0) counts them as "cap-row well pins (expected)".
    Tapeout-only leftovers: init's `verifyWellTap` reports 6 violations, and
    2 real M2 EOL DRCs on fw4 dp 4×4 RV; Calibre never ran.
  - **Floating M3 stubs (dp only).** 101 and 206 opens are 0.096 × 1.144 µm M3
    VDD/VSS stripe pieces between the SRAM's M3 PG-only halo (to y 112.124)
    and the core top. The tall dual-port macros leave no row there, so the
    pieces cross no followpin.
    Fix: `editTrim -type float -nets $power_nets -layers M3` at the end of
    `common/custom-power-leaf/outputs/power-strategy-dualmesh.tcl` (garnet
    9cfaa55d, in catch; it removes only unconnected wires, so tiles without
    stubs are unchanged). **Verified on gf12** (pg_diag v2 2026-10-11, Innovus
    22.13, in memory): dp opens 109 → 7 and 214 → 7. It removed exactly the
    101/206 stubs, and all VDD opens are gone; the sp tile is unchanged (111
    M3 wires before and after). It applies to power steps run after the
    pull. Already-built dp tiles keep the stubs, which is harmless for area
    and power.

  Re-dropping M1..M3 power vias closes nothing. Forcing them
  (`ignore_DRC true`) adds 248–1503 vias, still closes nothing, and creates
  real V2/M2/M3 DRC. Full verify_drc (limit 100000) is 1122–1135 violations,
  all wire vs routing blockage. The only real geometry is 2 M2 same-mask EOL
  spacing on fw4 dp 4×4 RV.
  **`mflowgen/bin/pg_diag.sh <out> <workspace>...`** (garnet 72894fb0, v2
  17671722) is read-only. It restores each workspace's signoff checkpoint
  from `<out>/<name>/` (never saved) and writes:
  - `summary.txt`;
  - `opens.txt`: per open, the wires/vias/cells/blockages in its box;
  - `cells.txt`: PG pin shapes of the cells on opens and of all COLCAPs;
  - `adk_endcaps.txt`: the ADK's endcap procs;
  - `drc_summary.txt`: verify_drc split into blockage artifacts vs real;
    `PG_DIAG_DRC=0` skips it;
  - `trials.txt`: `PG_DIAG_TRIALS`, any of `trim pins vias`, applied in order.

  It packs them into `<out>.tgz`. Innovus 22.13 runs it fine.
- **Rerun (zip `STANDALONE_r8cad-gf12_20261008-202805`, started 20:14, garnet
  before 546b1e46/d79bf443, so 3 modes and no DRC/conn .rpt in the zip):**
  standalone `--standalone-only --fresh`, then tile `--clean-stale` (signoff,
  PT and PnR power rebuilt). PT signoff now reads the whole SDC: PBA WNS
  −11.4 ps (In2Out, the `tile_pnr_setup_wns_ns` column = PBA top-100), GBA
  `report_global_timing` −25.2 ps (Reg2Reg ×10, In2Reg −14.8, In2Out −11.4),
  hold met; Innovus still −90 ps / 9 VSS opens / 1000 DRC. Tile power
  unchanged (synth 1.59 / 10.5 mW, PnR 2.04 / 11.6 mW, 100% annotated, sims
  PASS). Two failures, both fixed after the run: (1) genlibdb's `'Error:'`
  postcondition, from 9 SEL-005 (no split-FIFO regs under
  `USE_NON_SPLIT_FIFOS`; lib/db were written) — garnet 8baba3c4; (2) lake
  standalone ptpx-synth-{idle,active}: the netlist sims PASS and 99.96% of nets are
  annotated (idle 0.143 / active 1.08 mW, 7.6x), but read_sdc stopped at
  Genus's first of 155 `set_dont_use` lines (the SDC's tail: nothing but
  the other 154 was lost; this Genus SDC has no `set_load` at all) and the
  "Errors reading SDC" postcondition failed —
  read_sdc_compat drops synthesis-only directives since lake 5ed60bd1 /
  garnet 1eba1483. Rerun: pull garnet + lake; standalone `--standalone-only
  --make "clean-synopsys-ptpx-synth-idle-power
  clean-synopsys-ptpx-synth-active-power"`, then `--standalone-only
  --memtile-power`; tile `--clean custom-genlibdb-constraints` (rebuilds
  genlibdb + lib2db) with `--zip --zip-slim`. **Verified** in the re-zip
  `STANDALONE_r8cad-gf12_20261008-215342` (2026-10-08): genlibdb 0 errors,
  lib2db built, both standalone ptpx postconditions pass (dropped 1
  current_design + 155 set_dont_use), power identical to 3 digits.
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
  `<--graph>/construct.py`, or `--clock-mhz` (2026-10-11); override
  `--standalone-clock-ps`. The 1.1 ns PnR
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
  case-analysis when absent. **One timing mode for spec MemCores (2026-10-08,
  user decision):** without the case analysis FIFO and SRAM were copies of
  UNIFIED_BUFFER, synthesized and PnR-timed 3x. With no `mode[0]` Genus now
  creates only UNIFIED_BUFFER; `custom-genus-scripts/copy_sdc.tcl` links only
  the `syn_out.cstr_mode_*.sdc` Genus wrote, and `custom-flowgen-setup/
  setup.tcl` builds analysis views for the `inputs/sdc/*.sdc` present (all
  three if none). The onyx MemCore (mode pin) keeps 3 modes + 6 case analyses
  (checked in tclsh with stubbed Genus commands against the old script). Only
  script content changed, so built workspaces keep their 3 modes until synth
  is rebuilt (same constraints, so same timing).
  What `mode` selects (lake `memtile_builder.finalize_controllers`: one value per
  non-exclusive controller, in `util_onyx` append order; StencilValid is
  exclusive, on `mode_excl`): spec MemTile 1-bit `mode` 0 = spec controller,
  1 = StrgRAM (ROMs: camera_pipeline_2x2 has 12, unsharp 1; needed). The one
  unpinned mode times both. Onyx `mode[1:0]` 0 = FiberAccess (sparse),
  1 = StrgUBVec, 2 = StrgRAM, so its constraint-mode names are legacy:
  "UNIFIED_BUFFER" pins sparse, "FIFO" pins UB, and no FIFO controller exists.
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
  Routing: since garnet e30c6792 (2026-10-11) the fabric is built at the
  spec's data width, so every spec port is one (dw+1)-bit core pin on the
  fabric's data track (`max(ic.get_bit_widths())`, e.g. B33 at dw32) ->
  input k on WEST track k, output k on EAST track k (pipeline reg bypassed);
  input_data.hex digits and the tb `stim` width follow the track width.
  Bit-blasting is kept only for tile RTL built before e30c6792: there a
  non-16-bit port (dw 8/32/64 thesis points, ~20% of the set) was split by
  MemoryTileBuilder onto 1-bit core pins `port_<i>_<bit>` (+ 1-bit
  `port_<i>_valid/_ready`) -> data bits spread over the 20 1-bit tracks
  (shared once they run out: correlated but toggling), valid/ready pins on one
  track held at 1, the unused comply_17 MSB on a quiet track; output bits take
  free 1-bit SB_OUTs, interleaved across ports, the rest unobserved. Unused SB
  outputs and CBs whose default source is a random track get their select
  moved to a static one -- an undriven track, else the track held at 1
  (old bit-blasted tiles drive nearly every 1-bit track) -- select only, no
  RV `_enable`; any left on a random source are listed as `unquieted_muxes`
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
  the tb; track-major). The word goes on the port's (dw+1)-bit track (bit dw =
  unused comply_17 bit, 0). On pre-e30c6792 bit-blasted ports, bit b of the
  word goes on its track (a shared track carries its first pin's bit).
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
1/2/4/8; 1×1, 2×2, 4×4; dw 8/16/32/64 (bit-blasted, pre-e30c6792 RTL; the
whole-word tracks were checked by a16b3973 on dw 8/32/64); dims 1/2/4/6 with
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
**On gf12 (dw16 sweep, zip `NEW_SWEEP_r8cad-gf12_20261009-132919`, checked
2026-10-09):** 172 configs (static + RV). All 368 power sims PASS (172 synth
× 2 variants + 12 PnR × 2). All 368 PT runs are 100% annotated with no SDC
errors. Synth-level active/idle is 3.4–15.9× (median 6.7); PnR-level is
4.3–8.1×. Idle is 0.55–3.5 mW at synth; active is 4.8–22 mW. The window is
1000 cycles, except two short-domain specs (235 / 272 cycles). The docker
path is still unexercised.

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
A private tree = a dir of symlinks to every `/aha` entry except `garnet`
(its own `git clone`), plus a private app copy under
`Halide-to-Hardware/apps/hardware_benchmarks/<x>/<app>` (same `../../hw_support`
depth), so static and RV bundles can run concurrently (~26 / ~33 min at 16x16).
A dual-port spec (`dual_port: true`) also gets garnet's `--dual-port` for the build
and `aha pnr` (`spec_garnet_flags`, 2026-10-14; lake `resolve_memports` IndexErrors
without it; the tile graphs get it from `DUAL_PORT`): conv_3_3 on
`fw2_dw16_sc4096_dp_in2_out2_vc2` bit-accurate with it.

**Pipeclean bundles (2026-10-11/12, session 1fa8a391):** conv_3_3 on
`fw4_dw16_sc8192_sp_in2_out2_vc2` and `..._vc2_rv` (16x16), packed as
`/aha/sweep_out/app_bundles_pipeclean_lakee4fabdc1.tgz`; `aha test`
bit-accurate (3844 words). Static: recorded on lake fe2e786d (the port-order
fix before its rebase onto c357c6f7 = e4fabdc1; c357c6f7 only touches the RV
pond and bitstream encoding) + garnet a881563f. RV: re-recorded 2026-10-12 on
lake e4fabdc1 (c357c6f7's 12-bit RV pond; the 10-11 RV bundle's PE tiles were
stale: pond config_memory 557 vs 573) + garnet 2fc80dd6. Verified against
4x2 `--no-pd` builds from lake e4fabdc1 with other hash seeds (= what the build
machine builds; tile modules do not depend on the array size):
`check_bundle.py` OK and 0 replay mismatches on every tile (static 2 MEM + 10
PE over 7539 cycles on a no-spec build = Tile_PE's default; RV 1 MEM + 10 PE
over 8843 on an RV build = Tile_PE with the RV spec knobs). Two earlier sets
were deleted as stale (lake 04191ea5: before 144e2062's comparator pruning;
144e2062: before the port-order fix).

**dw16 app-bundle set (2026-10-14/16, session 1fa8a391; user scope).** conv_3_3, gaussian,
harris_color and pond matmul (`tests/matmul_rvtry3` n=16, `-enable_ponds`) x the 12
`dw16_pnr12` configs, 16x16, `--cgra-tiles`, RV without `--rv-balance`; static bundles with a
static spec pond (`--pond-spec {}`, so one Tile_PE per config serves every app). Recorded in 6
private slot trees (garnet 495cf23f + the `--dual-port` fix, lake snapshot 11967ce5 on
PYTHONPATH; runner + logs: scratchpad 1fa8a391 `bigset/`). Result: 32 bundles over 10 configs,
8 per app, all `aha test` bit-accurate; `/aha/sweep_out/app_bundles_dw16_20261014/<app>/<config>`
(+ `STATUS.txt`, tarball `app_bundles_dw16_20261014.tgz`). Power: `cgra_app_power.py
--any-config --variants conv=..,gauss=..,harris=..,mmpond=.. --clock-mhz 400`.
Failures (OPEN_ISSUES ids):
- fw1 single-port STATIC line buffers (`clockwork/static-mem-bandwidth-unchecked`): each row bank
  is written and read every cycle (stride 1, overlapping) = 2 accesses/cycle on a 1-access SRAM;
  clockwork emits it, output wrong (conv_3_3 all 3844 ~half of gold). Pond matmul passes there.
- fw1 single-port RV (`garnet/fw1-sp-rv-netlist`), every app incl. pond matmul: PnR KeyError in
  `mapper/netlist_util.py` (an unconnected 1-bit `delay_reg` from clockwork, then an output
  `$reg1` missing from `nodes_to_ids`). Not bandwidth: lake's RV single-port arbiter would cope.
- Static pond matmul on fw8 sc32768 and fw4 vc4 (`clockwork/static-matmul-wide-mem`): wrong
  output. Not a constant offset (gold + 7824 only at some indices; an earlier note said all):
  within each output row the sim value steps by a constant per column (2040 in row 0, 2280 in
  row 1), as if one operand were read as a ramp. Not pond packing: the mismatches are identical
  with garnet b6dfabb7 (2026-10-17). RV passes.
- No-pond matmul (`matmul_rvtry3 sched=1`, reduction unrolled into a PE adder tree, no ponds):
  static `garnet_single_port_ram_schedule` assert; RV compiles (23 PEs) but does not route on
  16x16. In-place MEM accumulation is not a target (user, 2026-09-29). User decision pending.
- harris_color takes 1.5-2.5 h per bundle (sim); RV PnR of gaussian on fw2 dp took ~1 h.

**Bundle guards (garnet a881563f, 2026-10-11, session 1fa8a391; tests:
`tests/test_app_bundle_guards`, 25).** Both failure modes used to be silent:
- *Bundle recorded on another tile* -> `application` fails up front. The step
  gets the rtl step's `design.v` (Tile_MemCore + Tile_PE wire it; an
  unconnected input elsewhere only warns) and `check_bundle.py --design-v
  --design-name $design_name` compares the tile module's ports with
  `tile_ports.json` and, for Tile_MemCore, the lake controller's
  (`lakespec(_mem)?(_flat)?`) ports with `core_ports.json`, as {name: width}.
  Spec + mode alone missed lake 144e2062 (same spec, pruned RV comparators,
  config_memory 1621 -> 1421 bits for fw4 sc8192 rv): an old-network RV build
  now fails with `config_memory 1421 -> 1621`; a static build vs an RV bundle
  fails on the controller module + ports. For Tile_PE it always
  compares the pond module + ports with the bundle's own `garnet.v.gz`.
  **RV bundles on Tile_PE (2026-10-12):** an RV-mode CGRA's PE tile carries
  the RV spec pond (`lakespec_pond`), so build Tile_PE with
  `LAKE_SPEC_CONFIG` / `LAKE_SPEC_MODE` = the bundle's spec + mode (the rtl
  step forwards them to garnet.py; the application step then also checks spec
  + mode). Unset = the default PE tile (`PondTop`), which matches static
  bundles. A mismatch fails with a hint saying so.
- *Tile that does not replay the recording* -> tile-post-{rtl,synth,pnr}-power
  fail at the end. `run_all_tiles.py` (one file, three identical copies; a test
  checks) writes per tile `outputs/reports/<tile>.replay.json` (the tb's `cycle
  N: <port>: got X, expected Y` lines, sim reached `$finish`, power report
  present) and `replay_summary.txt`. Param `replay_check` (env `REPLAY_CHECK`
  through the tile graphs): `auto` (default) = fail with an app bundle, warn on
  the legacy stock-container path; `fail`; `warn`. Reports are written first.
  `memtile_power.csv`: `tile_{rtl,synth,pnr}_replay_exact` = `<exact>/<tiles>`.
  Each failing tile also gets `<tile>.mismatches.txt` (first 5000 lines; in the
  zip) and its replay.json says how many were X/Z and the cycle span.
- **Power window of a tile the app never stalls (2026-10-14, session cfc4174c).**
  `common/testbench/cmd.tcl` opened the SAIF at the third `stall` change (time-0 init,
  stall 1, stall 0). The GLB stalls only the columns the app uses, so a `--cgra-tiles`
  idle (or route) tile in another column records stall 0 throughout. Its sim then ran
  to `$finish` with no SAIF ("no power report", replay `8/9`): conv_3_3 A's idle MEM
  `Tile_X0F_Y10` on gf12. B's idle tile at the same spot toggles, because its IO
  placement covers that column. Now bundle testbenches (`hold_reset`, with a stall
  input) get `saif_window = (pt_addr >= app_window)`. `app_window` is the tile's first
  stall release (1 then 0) found in its own vectors, so it rises in the timestep stall
  falls. A tile that never releases uses `stall_release`: the vector where most of the
  design's other tiles release (`generate_testbench.py` `stall_release()` on their
  simvisdbutil CSVs). With none, it falls back to the app's first flush, else the
  first reset. `cmd.tcl` stops on `saif_window == 1` when the testbench has it, and the
  legacy testbench keeps the stall-count window. Two Xcelium details:
  - The condition must reach `stop` unsubstituted (`[format {#%s...} ...]`): in a
    double-quoted string xmsim replaces `#<object>` with its value.
  - `stop -object` also fires at the time-0 init.

  Checked on /aha at RTL (bundle A MEM, old vs new tb + cmd.tcl): the placed tile's
  SAIF window is identical, and the idle tile gets one. Also checked at gate level by
  session 1fa8a391: on the freepdk45 netlist of the static pipeclean X07_Y05 (SDF, flops
  X until reset) the stop fires once, at the same instant as the legacy three-stop path,
  with no time-0 stop and an identical SAIF DURATION. A recorded GLB release cycle in
  the manifest would not help: vectors are simvisdbutil rows, not cycles (an idle tile
  has 2 fewer).
- **gf12 runs (2026-10-13, build machine, synth level; RTL level passed).**
  Both failed the check, as they should have: every MEM tile's outputs X at
  cycles 0-1, and the static conv_3_3 line-buffer tile `Tile_X07_Y05` X
  (`0xxxx` vs `00000`) on 3 B17 outputs for 1191 cycles from cycle 1201; the
  RV tile only the former. Run 1's diagnosis (garnet a14c789a: SDF notifiers,
  unwritten SRAM words) was wrong; run 2 had its `-nonotifier
  +define+IVCS_INIT_MEM` and failed identically. Real causes (run 2 zip
  `/aha/app_power_pipeclean_r8cad-gf12_20261013-201721.zip`):
  (1) the gf12 gate-level flops are X until the tile's first reset (recorded at
  cycle 2) despite `-xminitialize 0 -delay_udp_xminitialize` (freepdk45 cells do
  get zeroed; why gf12's do not is unknown). The recording ran from simulator
  zero-init. Knock-on: the MEM SRAM's clock is `gclk = clk & tile_en` (config
  flop), X at the first edge, so the gf12 macro model invalidates its whole
  array ("CLK input is unknown. Array contents are now invalid", t = 1 ns).
  (2) X07_Y05's X is not SRAM data: in static mode output port 3 reads its
  PISO `vec_storage` (lake `SingleBankStorage`, 2x64 flops, no reset)
  combinationally once config sets bypass; it holds X until the app's first
  write. The app starts at the first flush (cycle 2404); the recording
  zero-initialized it to 0.
  All "Timing violation"s (135-144/tile) are in the testbench's last partial
  cycle (inputs read past the vector array: X), not at startup.
  **Fix (garnet, 2026-10-13):** bundle testbenches (`generate_testbench.py`
  `hold_reset`) drive reset from time 0 until the recording's first reset,
  start the clock after 4 periods (an SDF reset tree can take a period),
  check outputs only from that cycle (`checked_from`) and print the app start
  (first flush after it, `app_start`). `run_all_tiles.py` counts an X/Z output
  with a known recorded value before the app start as `pre_app_x` (summary line
  + replay.json, not a failure); known-value mismatches anywhere and X after
  the app start still fail. `-nonotifier` and `IVCS_INIT_MEM` stay (`app_replay`
  param; keep the macro's array = the recording's zero-init SRAM). Verified on
  /aha (session 1fa8a391 scratchpad `prereset/`) by emulating the gf12
  conditions: the static bundle's Tile_MemCore through Genus (freepdk45, SRAM
  black-boxed), gate sim + SDF without `-delay_udp_xminitialize` (flops X until
  reset), SRAM = behavioral model zeroed like IVCS_INIT_MEM, invalidated on an
  X clock, with clk-to-Q (without it the model races the netlist's delayed
  clocks: 7660 off-by-one-read mismatches, an artifact). Old tb: X03_Y02 240 X
  mismatches at cycles 0-1, X07_Y05 3840 (gf12: 240 / 3804); new tb: 0
  mismatches on both, X07_Y05 3564 `pre_app_x` (= gf12's count after cycle 1),
  no X clock until the last partial cycle. Zero-init flops + old tb: 0. RTL
  emulation (no `-xminitialize`), static MEM + 3 PE tiles: new tb 0 mismatches.
  Limit: a static app whose output shows reset-less storage after its flush
  still fails; then make the gf12 flops zero-init instead (the tile sim's
  `logs/xminit.log` on the build machine says what `-xminitialize` covered).
  mflowgen exports params unquoted, so a param value with spaces breaks
  `mflowgen-run`: use a flag (as `app_replay` does).
- **gf12 run 3 (2026-10-13/14, garnet db83c42f; zip
  `/aha/app_power_pipeclean_r8cad-gf12_20261013-232235.zip`):** static passes
  at RTL, synth and PnR (X07_Y05: 3564 `pre_app_x`); RV passes at RTL and
  synth, fails at PnR: 26123 known-value mismatches from cycle 2310 (`valid`s
  1 where the recording has 0), 16 hold/setup violations, all on config
  registers (MemCore, SB B17) during configuration. Cause: the testbench drove
  every input 0.2 ns after its edge (`ASSIGNMENT_DELAY`), but the PnR netlist
  sees its clock ~0.208 ns after it (clock tree), and the tile SDC
  (`constraints/common.tcl`) has the passthrough inputs (`stall`, `config_*`,
  `reset`, `flush`, `read_config_data_in`) arrive at `pt_i_delay` = 0.7 ns, so
  PnR fixed hold for 0.7 ns: config data raced the clock (static's run had 3
  such violations and was lucky). Synth level has an ideal clock. **Fix
  (garnet, 2026-10-14):** bundle testbenches (`sdc_inputs`) drive each input at
  its SDC arrival: passthrough at `PT_INPUT_DELAY_NS` = 0.7, the rest at
  `INPUT_DELAY_FRACTION` x period (MEM 0.2, PE 0.3 = onyx `i_delay`), through
  `pt_addr` / `in_addr`; `test_vector_addr` (checks, bookkeeping) is unchanged.
  `test_testbench_sdc_input_timing_matches_constraints` fails if the constants
  drift from either tile's `common.tcl`. Verified by delaying the DUT clock
  0.5 ns in the local gate emulation: db83c42f's tb 22753 / 38012 known-value
  mismatches (X03_Y02 / X07_Y05; 182 / 864 violations), new tb 0 / 0 (no
  violations, 3564 pre-app X); without the delay also 0 / 0.
- **gf12 run 4 (2026-10-14, garnet >= dd8d9816; zip
  `/aha/app_power_pipeclean_r8cad-gf12_20261014-092703.zip`): MEM pipeclean
  passes.** All 6 replays exact (static 2 tiles, RV 1, each at RTL, synth and
  PnR), 0 timing violations, no SRAM X clock. RV Tile_X03_Y03: synth 5.44 /
  PnR 5.96 mW (SRAM 3.15 / 3.08); RV idle/active synth 1.40 / 10.9, PnR 1.88 /
  11.9. Static numbers = run 3 (below).
- **Whole placed CGRA, gf12 synth, 750 MHz (`cgra_app_power.py`, 2026-10-14,
  zip `/aha/cgra_app_power_pipeclean_r8cad-gf12_20261014-130646.zip`):**
  static conv_3_3 16x16: all 12 placed tiles replay exactly; 25.45 mW = MEM
  7.89 (2 tiles) + PE 17.56 (10 tiles, 0.66-3.74 each), SRAM 4.05; window
  6.87 us = 175 nJ per run. MEM tiles = the sweep's run 4 numbers exactly. RV:
  MEM 5.44 mW; the RV Tile_PE workspace ran on garnet 58ff4c8e, before
  03833f4f's pond-path constraints fix, so Genus stopped at TUI-61: rerun it
  with `--config <rv> --clean constraints`.
- **RTL-level power on gf12 is not usable (OPEN_ISSUES
  garnet/rtl-level-power-annotation):** PT annotates 60% of nets / 20% of leaf
  cells from the RTL SAIF (synth, PnR: 100%; freepdk45 locally: 100%), so it
  defaults the rest. Run 3, static, replays exact at all levels (mW, tile
  total / SRAM macros): X07_Y05 (line buffer) RTL 3.42 / 0.05, synth 6.38 /
  4.03, PnR 6.98 / 3.84; X03_Y02 RTL 3.28, synth 1.51, PnR 2.06. Idle/active
  (`--memtile-power`): synth 1.59 / 11.1, PnR 2.13 / 12.3. Use synth/PnR.
- Power domains: the tile graphs pass `garnet.py --no-pd` (`pwr_aware =
  False`), `gen_app_bundle.py` does not. Today that changes nothing:
  `--no-pd` is a no-op (OPEN_ISSUES `garnet/no-pd-tuple`, a trailing-comma
  tuple in `cgra/util_onyx.py`), so every build, the bundles' and mine
  included, has power domains, and the 0-mismatch replays on `--no-pd` 4x2
  tiles say nothing about PD-less tiles. If that bug is fixed, re-check: tile
  ports are compared by `check_bundle.py`; a moved config register shows up as
  replay mismatches.

**garnet.v run-to-run determinism (functional part fixed in lake e4fabdc1).**
kratos `get_port_names()` is a Python set and lake iterated it unsorted, so
`CoreCombinerCore`'s read-only configs (pass-through inputs of the core's
`read_config_data` mux) came in hash-seed order: module `PE`'s
`mux_aoi_10_32_inst0` I[7] was the reduce cluster's `onyxpeintf_O2`/`O3`/`O4`/`O4`
in four builds, while RTL (`garnet.py --verilog`) and bitstream (`aha pnr`)
are separate processes. Fixed: 4x2 builds under PYTHONHASHSEED 1 and 2 differ
in 0 lines after normalizing (strip trailing commas, sort; 6 before). Still
textually different (port-connection order from kratos `util.to_magma`, kratos
C++ FSM default-assignment order), so compare two garnet.v that way, never by
md5. The build machine's rtl step uses the container's kratos but the host's
lake (copied in), so a lake pull brings the fix there.
Tile_PE has no `use_non_split_fifos` param, but that is fine:
`common/rtl/gen_rtl.sh` passes `--use-non-split-fifos` to garnet.py
unconditionally, so every tile graph builds the non-split switch-box FIFOs the
bundles record (canal `circuit.py` builds `FifoRegWrapper` per that env; it
changes RTL, not just the bitstream).

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

The old `--per-tile` flag (powered only the lake memory core in isolation, via
lake `pd/thesis/roundtrip-power`; never wired into the graph) was deleted on
2026-10-08 with its untracked `common/tile-per-tile-power` step (user
decision): bundles cover the whole tile (interconnect + config) for MEM and PE
tiles at all three power levels.

### Whole-CGRA power of app variants: `cgra_app_power.py` (2026-10-13, session cfc4174c)

Several recorded app runs ("variants", e.g. two mappings of one app) replayed on
the SAME synthesized Tile_MemCore and Tile_PE, so they differ only by activity,
then summed over the array. Made for the conv_3_3 A/B study (eat the first two
rows at the output vs up front through the MEM's filter path; lake CLAUDE.md §6
"filter path"), and reusable for any set of bundles of one spec + mode.

    # /aha: record the bundles (two private aha trees, both variants at once, ~35 min)
    mflowgen/common/application/conv_3_3_ab_bundles.sh <root>      # -> <root>/{A,B}/<config>
    # build machine: one synth per tile, every variant replayed on it
    ./mflowgen/cgra_app_power.py --variants A=<root>/A,B=<root>/B --out-dir <dir> [--zip]

- **Graph**: env `APP_BUNDLE_VARIANTS="A=<bundle>,B=<bundle>"` makes
  Tile_MemCore / Tile_PE add per variant `application-<v>` -> `testbench-<v>` ->
  `post-synth-power-<v>` (`common/app_variants.py`), wired like the graph's own
  chain (synth netlist, SRAM model on Tile_MemCore); the variant's app_bundle
  param is set after `g.update_params`. Unset: no steps added; checked that every
  step script of both graphs is identical to before (freepdk45 materialization).
  Variants force `pwr_aware = False` like SYNTH_POWER.
- **Driver** (`cgra_app_power.py`): per config every variant has
  (`<dir>/<config>/manifest.json`; spec, mode and pond spec must match), one
  workspace per tile graph (`<out-dir>/<config>/<tile>`, MEM and PE built at
  once, `--tile-jobs`), env as sweep_specs' `_tile_env` (+ `SYNTH_POWER`,
  the variants; Tile_PE gets the spec env only for RV bundles), then `make
  post-synth-power-<v>...`. **One clock for the array**: `--clock-mhz`
  (default 750) sets Tile_MemCore `CLOCK_PERIOD` and Tile_PE `clock_period_PE`
  (their own defaults differ: 1.333 / 1.1 ns). `--clean rtl` after a lake/garnet
  pull; `--report-only` re-reads workspaces; `--zip` packs CSVs, per-tile
  reports, xrun logs and synth area (no workspaces).
  `--any-config` (2026-10-16, session 1fa8a391): run every config ANY variant has, each with
  only the variants that have it (default: only configs every variant has). For one variant
  per app where some apps fail on some specs (the dw16 app-bundle set).
  A bundle recorded with `--pond-spec` (manifest `pond_spec`) gets its Tile_PE
  built with that pond (`LAKE_POND_SPEC_CONFIG` = `<ws>/pond_spec.json`;
  2026-10-14, session 1fa8a391): before, it replayed on the default PE tile
  and check_bundle failed on the pond.
- **Outputs**: `cgra_power_tiles.csv` (per replayed tile: role, int/switch/leak/total
  W, SRAM macro W, window, energy, replay exact) and `cgra_power.csv` (per config x
  variant): `<tile>_{placed,route}_{n,W}`, `app_W` (placed + route), `sram_W` (cell
  rows matching `--sram-cell-re`, default gf12 `^IN12LP_`), `window_s`, `app_J` (sum of
  each tile's power x window = energy per app run), `idle_W` / `array_W` / `array_J`
  (+ one idle tile per type x the tiles the app does not touch), `d_*_pct` vs the first
  variant. The activity window is the SAIF window: last stall release
  (`stop stall_toggle ... = 0`, common/testbench/cmd.tcl) to `$finish`. Averages
  differ from energies when variants run for different times: in the old freepdk45
  recordings B's window was 10% longer than A's.
- **Route and idle tiles** (`gen_app_bundle.py --cgra-tiles`): the bundle also probes
  every MEM/PE tile a route passes through without a placed core (design.route `PORT`
  / `RMUX` / `SB` / `REG` coordinates; list name `route`) and the last untouched tile of
  each type (name `idle`); the manifest gains `array_tiles` (Interconnect tile counts)
  and `cgra_tiles`. Without the flag the totals cover placed tiles only (array columns
  empty). IO tiles and the GLB are not counted.
- The per-tile power sub-graphs now also copy PT's `-leaf` cell report
  (`<tile>.cell`; synth and PnR levels, not RTL: ptpx-rtl writes none) for the
  SRAM split.
- **conv_3_3 A/B spec**: `--spec-set filter_fifo` = `fw4_dw16_sc8192_sp_in2_out2_vc2_ff8_rv`
  (lake `build_spec_rv(filter_fifo_depth=8)`; `_ff<N>` in config names; static
  configs with the key are skipped). Variant B needs MetaMapper with
  `METAMAPPER_MEM_PORTS=3` (cgralib.Mem with the filter pair as a third in/out) and
  the pre-PnR hook `common/application/hooks/conv_3_3_eat_rows_up_front.py`;
  `conv_3_3_ab_bundles.sh` sets both.
- Tests: `tests/test_app_bundle_guards/test_cgra_app_power.py` (env parsing, route/idle
  tiles, report parsing, sums, idle scaling).
- **Replay fix found with the idle tiles (garnet, after 71bcfde3):** `generate_testbench.py`
  makes ONE testbench for all of a design's tiles and used the FIRST tile's vector count.
  simvisdbutil writes a row per value change while the clock is high, so a tile whose
  probed signals change mid-cycle gets extra rows (conv_3_3 A: placed/route tiles 8843,
  the idle tiles 8841 with the same 8841 clock edges); the shorter tile then ran past the
  end of its files (82 "ready got 1, expected 0" lines at the last 2 cycles: a replay
  FAIL). Now the testbench takes the longest count and shorter tiles' files get their
  last vector repeated (`pad_vectors`, `@file_info` line). Equal counts: unchanged.
- **Local check of the conv_3_3 bundles (2026-10-13):** every tile of the unbalanced A
  and B (ff8) bundles replayed exactly at RTL (session 1fa8a391's `validate.sh`:
  generate_testbench on the bundle + xrun of the bundle's garnet.v tile modules), but
  they ran at different rates (A 0.750, B 0.667 tokens/cycle: 5,533 vs 6,167 ns), so
  their power did not compare like for like. Superseded by the balanced bundles below.
- **Balanced A/B (2026-10-14, `--rv-balance 8`, now the recorder's default):** both at
  one token per cycle, bit-accurate in `aha test`, and every tile replays exactly (A 41
  tiles: 9 MEM + 32 PE; B 54: 12 + 42):

  | | A | B |
  |---|---:|---:|
  | outputs / cycles at the output IO | 4,096 / 4,097 | 3,968 / 3,969 |
  | total time | 4,173 ns | 4,189 ns |
  | padding registers + PE output FIFOs | 27 + 3 | 45 + 4 |
  | SRAM read cycles | 3,204 | 1,984 |

  Package: `/aha/sweep_out/fp_fifo_20261013/conv_3_3_ab_bundles.tgz` (ff8 only: the
  FIFO depth did not change any rate).

### RV branch balancing: `gen_app_bundle.py --rv-balance N` (2026-10-14, session cfc4174c)

Dense RV runs below one token per cycle whenever a fork's branches rejoin at a PE with
different latencies. Root cause and mechanics are in archipelago CLAUDE.md "Dense RV
throughput"; in short: every hop has a register (`EXHAUSTIVE_PIPE`), registers are
canal `RegFIFO` depth 2 with `ready = ~full`, fanouts are lazy forks, and RV maps with
`MATCH_BRANCH_DELAY=0` / `PIPELINED=0`. So full rate needs the stage counts of the
branches to match exactly at every join (conv_3_3: A 0.750, B 0.667 before).

- **Model** (`common/application/rv_throughput.py`): token-level simulation of the
  routed graph (design.route/place/design_top): REG = 2-deep FIFO with `extra_data`
  initial tokens, PE input/output FIFOs of 2, an optional 2-deep primitive output FIFO,
  lazy forks, MEM outputs / input IO / constant PEs always valid, MEM inputs / output IO
  always ready. Matches xrun on 6 PnR results (0.750 / 0.667 / 0.722 / 0.765 unbalanced,
  1.000 balanced). `python rv_throughput.py <app>/bin` prints the rate and the next step.
- **Loop** (`rv_balance()` in gen_app_bundle.py), per round while below 0.995:
  1. **Parity:** with endpoints pinned, any route between two tiles has a stage count of
     fixed parity (every hop registered, Manhattan lengths share parity), so padding can
     only add an even number of stages. `parity_outfifo` picks the PEs whose primitive
     output FIFO to enable (+1 stage; onyx_pe `bypass_prim_outfifo = 0`, which dense RV
     otherwise sets to 1) so every join's mismatch is even. Fewest odd mismatches, then
     smallest total, then fewest PEs, over all sets of at most 6 PEs (exhaustive).
     Written to `bin/PE_fifos_bypass_config.json` as `"prim_outfifo_bypass": 0`, read by
     `memory_core/core_combiner_core.py`. Bitstream only, no placement change.
  2. **Absolute latency matching** (`balance_plan_abs`): an input arriving d stages
     early gets (registers on its unshared route now) + d padding registers. Absolute
     because the router puts padding registers on hops that were already registered:
     an incremental "+d" mostly adds nothing.
  3. Padding is inserted by `hooks/rv_balance_branches.py --plan` (plain `coreir.reg`,
     `extra_data 0`, so data is unchanged), named `rv_balance_<md5(input)[:8]>_<i>`.
  4. **Pinning:** every block and netlist register keeps its tile (`manual.place` +
     `MANUAL_PATH_BALANCE_PLACER=1`). Lines are instance names, because block ids change
     when registers are added (`global_buffer/io_placement.py` maps names through
     `id_to_name`, ignoring `@track`). Only new registers and PnR pipelining move.
  5. PnR again; if a later round got worse, the best round is rebuilt with its whole
     placement pinned.
  conv_3_3: A converged in 1 round, B in 2. Outputs: `work/rv_balance_{plan,log}.json`,
  `work/PE_fifos_bypass_config.json`, manifest `rv_balance`. The bin/ copy is removed at
  the end, because the bitstream is already made and a later unbalanced PnR must not
  pick it up.
- **Dead ends (do not retry):**
  - Bypassing PE input/output FIFOs (`fine_grain_fifo_bypass`) makes ready depend
    combinationally on valid. Through the lazy forks that forms a loop, and the sim hangs.
  - Pre-PnR depth balancing (`--pe-stages`) ignores routing registers.
  - Greedy and uniform padding oscillated or plateaued (0.80–0.91).
  - Unpinned re-PnR moves everything.
- **Needs** archipelago >= de8e844: `reg_into_route` used to patch only the first segment
  holding a hop, so an RMUX could get two inputs. The model refuses such routes
  (ValueError).
- **Limits:**
  - Refuses apps whose map writes their own `PE_fifos_bypass_config.json`
    (hack_design_top.py, pond feedback), because the model assumes every PE FIFO.
  - MEM inputs are not balanced, since a MEM decouples them.
  - Not wired into `aha regress` or `aha pnr`; bundles only.
- Tests: `tests/test_app_bundle_guards/test_cgra_app_power.py` (hook naming and
  idempotence, fork imbalance, parity output FIFO, placement).

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
- **Tile_PE constraints follow the pond (2026-10-14, session cfc4174c).**
  `Tile_PE/constraints/constraints.tcl` hard-coded the legacy pond's register file
  (`PondCore_inst0/PondTop_W_inst0/PondTop/memory_0/data_array_reg*`) for the
  config-to-pond multicycle paths. An RV PE tile (and a static one with
  `LAKE_POND_SPEC_CONFIG`) has the lake-spec pond at
  `PondCore_inst0/PondCore_inner_W_inst0/PondCore_inner/memory_0/data_array_reg*`, so
  `get_pins` was empty and `set_multicycle_path` aborted Genus with TUI-61. That was the
  first gf12 RV Tile_PE synth: cgra_app_power conv_3_3 A/B. The script now uses the
  path that exists and skips the MCP when none does (`--no-pond`). Checked locally with
  Genus 20.11 (freepdk45, the step's read/elaborate attributes, whole constraints.tcl):
  the RV tile from the A/B bundle picks the spec path, a static tile keeps the PondTop
  path, and neither has `Error   :`. Genus 21.16 segfaults at startup on /aha; use
  `module load genus/20.11.000` (it also sets the license path).
- **Why Tile_PE misses 1.333 ns (2026-10-14, session cfc4174c).** gf12 synth (session 1fa8a391's
  pipeclean, Genus 25.12): slack −1.117 ns RV / about −1.0 ns static, about −1.1 ns in every class
  (R2R, I2R, R2O, I2O), 1,766 failing paths, so the critical chain is about 2.45 ns (≈ 408 MHz).
  No path reports are in the cgra_app_power zips: they are in the synth step's
  `results_syn/final_time.rpt` on the build machine. A local Genus 20.11 freepdk45 run of the
  same RTL and constraints has the same worst register-to-register path in RV and static:
  pond register (RV: an iteration-domain counter, then `valid`) → CB → **through the PE's
  combinational ALU: BFloat16 FP compare (ChipWare `CW_fp_add`) → condition logic → 1-bit
  output** → SB mux → SB register. About 70% of it is inside the PE (3.1 of 4.5 ns locally),
  because the PE has no register between its input and output pins. The constraints'
  FP false paths (`set_false_path_if_pins_exist` on `PE_inst0/WrappedPE_inst0$PE_inst0/ALU_inst0/...`,
  the Amber hierarchy) match no pins on onyx ("pins=" in the log), and they would only cover I/O
  paths anyway. Local freepdk45 output-path slacks (about −47 ns) are an artifact: the ADK's
  `ADK_TYPICAL_ON_CHIP_LOAD` 7 is read as 7 pF. The conv_3_3 A/B gf12 rerun therefore uses
  `--clock-mhz 400`.
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
- GOTCHA: `tests/test_app/tb/kernel.sv` writes its input stream to the fixed path
  `/aha/garnet/tests/test_app/input_data.txt` (debug dump, lines ~344/385), so every
  `aha test`, from any tree, writes into the shared garnet checkout.

### Pond packing (2026-10-12, session 08555638; fixed in the commit that added this section, 2026-10-14)

Two bugs found by matmul_tile ux=4 (kernel in 4 broadcast-banked ponds). Both fixes were
verified in private trees at 2fc80dd6; the two functions are unchanged up to this commit
apart from pycodestyle spacing:
- `garnet.py` `pack_ponds` put a pond into the PE it shares the most inter-core
  connections with, with no limit per PE. The 4 kernel banks' only inter-core peer is the
  kernel PE (their outputs go to the multiply PEs on pond output 1, not an inter-core
  port, because `find_packing` gives each multiply PE's packed slot to its accumulator),
  so all 4 packed into that one PE's pond: `pes_with_packed_ponds` kept the last one, and
  every lane read bank 3 (static T44u4: lanes 0-2 = lane 3's sums). The pre-27da971d code
  had the same gap. Fix: grant claims strongest first, one pond per PE; a pond left without
  a PE stays unpacked (an `M` node placed on its own, like a path-balancing pond). Identical
  packing whenever every pond's best PE is distinct (static T84: bitstream identical);
  static T44u4/T84u4/T88u4 bit-accurate with it.
- `mapper/netlist_util.py` `swap_pond_ports` (pond output 0 <-> 1 for ponds `find_packing`
  did not pack) rebuilt the config from `in2regfile_0/1` + `regfile2out_0/1` only, which
  drops a dense-RV pond's program (`port_mappings`, `domain`, `access_map`, `filter`,
  `dep_values`, `rv_sched`): lake then built a static program and the RV pond's writer never
  got ready (waveform: input ready 0 from the flush on). Fix: keep every key, swap the
  `regfile2out_*` keys and the `data_out_pond_0/1` suffixes in `port_mappings` (lake's static
  conversion ignores `port_mappings`: static T44u4 bitstream identical).
- With both fixes, RV ux=4 still hangs: a standalone RV pond fed over the interconnect forms
  a valid/ready loop with the SB/CB lazy fork (lake/CLAUDE.md §6 "RV pond ready depends on
  valid").

## Fabric data width follows the spec's `data_width` (2026-10-06)

Before this, a spec with `data_width != 16` built a normal 16/17-bit fabric.
lake flattened the MemCore's (dw+1)-bit ports into dw+1 single-bit pins on the
1-bit network: 70 in + 71 out at dw32, a garnet.v of 5.0 MB vs 2.7 MB. So
**Tile_MemCore synth/PnR numbers for dw 8/32/64 specs built before this change
measure the wrong tile** (17-bit SB plus a bloated 1-bit SB). Re-running them is
the build-machine sweep in "dw 8/32/64 Tile_MemCore PPA" below (RTL pre-checked here). Now
`util_onyx.lake_spec_data_width()` (spec JSON, 16 without one) sets the whole
fabric:

- tracks `[1, dw+1]` (RV fabric; `[1, dw]` dense-only, which asserts dw == 16);
  switch-box pins `SB_*_B{dw+1}`, IO `glb2io_/io2glb_/f2io_/io2f_{dw+1}`;
- PE = lassen `gen_PE_fc(dw)`: the integer PE at dw bits with the same
  instruction layout (`inst` = 36 + 3·dw bits: 60/84/132/228), and **no bf16
  FPU / FP-custom units at dw != 16** (FP ops return 0); 16 is `PE_fc` itself;
- MEM: StrgRAM/StrgRAMRV `data_width=addr_width=dw`; at dw8 the ROM address
  (8 bits) is zero-extended, so it only reaches the low 256 words;
- pond: always a spec pond at dw (static `build_pond` / `build_pond_rv`); a
  `--lake-pond-spec-config` with another `data_width` raises;
- GLB `cgra_data_width=dw`, `lanes = 64/dw` per bank word (generic lane logic;
  the 4-lane blocks are kept for dw16). E64 / multi-bank / MU GLB and the
  matrix-unit IO are 16-bit only (asserted).
- lake side (token layout, legal widths, config word): lake CLAUDE.md §5.5.

Verified (scratchpad `a16b3973-.../scratchpad`): dw16 garnet.v byte-identical
to the pre-change tree under `PYTHONHASHSEED=0`, static + rv. Without a fixed
seed, garnet.v is NOT run-to-run deterministic: the no-spec build reorders
`scanner_pipe` FSM default assignments even between two runs of one tree, so
diff seeded builds. dw 8/32/64 static + rv were checked with
`tests/check_widths.py`, the GLB lanes in Xcelium, the lassen ALU against a
Python model, and the memtile power tests (whole-word B{dw+1} tracks now).

**Apps on dw 8/32/64 fabrics.** Committed 2026-10-11 (aha mek 30abb17: lassen 52f023e, lake 2f20b666, garnet e30c6792, Halide 571fba524, MetaMapper 373c5c0, archipelago 31285ac, clockwork 1cc6da51); applied to the shared trees on 2026-10-08
(Halide-to-Hardware, clockwork, MetaMapper, lassen, garnet, archipelago, aha). The shared
libHalide and libclkwrk.so were rebuilt. Shared-toolchain checks:
- 16-bit compile: byte-identical to before.
- dw32: gaussian RV.
- dw64: pointwise_wide static.
- dw8: gaussian8 RV.
- The commits above hold the current code. The scratchpad patches
  `a16b3973-.../scratchpad/p32/patches/*.patch` and the private tree `p32/aha` are the 2026-10-08
  env-knob version, superseded on 2026-10-10 (see "One source of truth" below).
- Driver: `s32/e2e2.sh` (`DW=`, `MODE=`, `FW=`, `APP=`, stages; `MAPSPEC=`/`MAPCOLL=` to
  compile against another spec or collateral). It runs the shared toolchain with a private
  garnet copy.
- **Results, bit-accurate:**
  - dw32: pointwise and pointwise_wide (4×4 static); gaussian static + RV, pointwise RV (8×8).
  - dw64 (fw2): pointwise and pointwise_wide static + RV, gaussian RV.
  - dw64 (fw4): gaussian static.
  - dw8: pointwise8 and gaussian8 static + RV. These are uint8 / bounded-value apps, since a
    16-bit app's values don't fit in 8 bits.
- **`pointwise_wide`** computes `uint16((uint32(in)*1000)>>4)`; a 16-bit datapath would get 3528
  of 4096 pixels wrong.
- **Static fw=2 line buffers (not a width issue):** static gaussian / conv_3_3 on a **fw=2** spec
  failed at dw16 and dw64 alike. Both clockwork root causes are fixed in clockwork 9fdfe6bf
  (pushed; aha mek d413f51), so gaussian static fw2 now passes at dw16 and dw64. See
  clockwork/CLAUDE.md "Static fw=2 line buffers".
- **One source of truth: the lake spec's `data_width`** (2026-10-10; this replaced the
  `CGRA_DATA_WIDTH` env knob, which nothing reads any more):
  - **Fabric:** garnet builds from `--lake-spec-config` (`lake_spec_data_width`). Tracks are
    [1, dw+1], or [1, dw] with `--dense-only`, the same as stock's 16/17.
  - **Compiler:** the spec's lake collateral carries `data_width` at every level (lake
    `Spec.extract_compiler_information`). Halide (`cgra_data_width()` in `CoreIRCompute.cpp`),
    clockwork (`cgra_data_width()` in `options.cpp` → `DATAPATH_WIDTH`), MetaMapper
    (`metamapper.data_width.data_width()`), `hardware_targets.mk` and `raw2txt.py` all read it
    from `LAKE_COLLATERAL_JSON_MEM`. Without one the width is 16.
  - **`aha map`:** sets the collateral before the first `make`. That matters because the Halide
    generator runs in `make compare`/`tree`, before `make map`. With no `--collateral` and
    `LAKE_SPEC_CONFIG` set, it generates the MEM collateral from that spec, the way the pond
    collateral comes from `LAKE_POND_SPEC_CONFIG`. It errors if the collateral, spec or pond
    collateral widths differ. See `aha/util/map.py` `set_lake_collaterals` and
    `aha/util/data_width.py`.
  - **PnR:** `Garnet.load_netlist` calls `set_data_width(self.data_width)` (MetaMapper's, via
    `mapper/netlist_util.py`), so the mapper and `netlist_util` work at the fabric width. It
    was in `Garnet.__init__` until 2026-10-12; moving it means RTL generation never needs
    MetaMapper's `data_width` (see "Container steps" below). `check_app_data_width` refuses
    an app whose top data ports are a different width. `aha pnr` passes the width to
    `parse_design_meta.py --data-width`.
  - **`aha test`:** reads `CGRA_DATA_WIDTH` from the GLB header garnet generated
    (`global_buffer/header/global_buffer_param.svh`). The testbench compiles that same header.
  - **Verified 2026-10-10 on the shared toolchain** (s32 tree, driver `s32/e2e2.sh`, which has
    no env knob):
    - Compile outputs (gaussian static, dw 8/16/32/64) are byte-identical to the old env-knob
      toolchain. Two known exceptions: 3ed21ea3's `port_mappings` fix (the old reference
      lacked it), and at dw8 MetaMapper node-id suffixes. The suffixes come from unsorted rule
      glob order, and the output is identical once they are normalized.
    - E2E bit-accurate: gaussian dw32 static + RV, dw64 fw2 static, dw16 static. Both mismatch
      errors fire.
  - **More checks 2026-10-11** (committed code, small arrays, `s32/e2e2.sh`), all bit-accurate:
    - dw32 static: `tests/{arith,ucomp,conv_2_1,boolean_ops,ternary,absolute,scomp}`
      (4×4), `tests/conv_3_3` fw2 (4×8), and `apps/scalar_reduction` (pond, 16×8).
    - dw32 RV: `tests/{arith,ucomp,conv_2_1}`, and `apps/pointwise` fw2.
    - dw64 RV fw2: `tests/{arith,conv_2_1}`.
    - dw8 RV: `tests/mem_transpose_test`.
  - **Expected differences:** `tests/{ushift,sshift}` at dw32 differ from the gold only above
    bit 15 (all 4096 pixels equal mod 2^16). Their uint16/int16 programs rely on 16-bit wrap,
    which a 32-bit PE does not do (see "arithmetic width" below).
  - **Min/max, ROMs and unsharp (later on 2026-10-11, private tree p32/p33 from the committed
    HEADs):** all bit-accurate:
    - `tests/{uminmax,sminmax}` at dw32 static. coreir f32ab1b9 dropped commonlib's
      width==16 asserts, and the rebuilt `libcoreir-commonlib.so` is installed.
    - `tests/rom` static at dw16 and dw32.
    - `apps/unsharp` at dw32, static + RV (16×8, `--glb_tile_mem_size 256`). This needed
      Halide 176cfdc04: `mult_middle`/`mult_high` are used only at 16, because on a W-bit PE
      they shift by W/2 and W.
    - With 128 KB GLB tiles, unsharp's 204 KB (32-bit) input ran into the output's GLB bank
      and came back wrong. The testbench (`tests/test_app/lib/map.c`
      `check_io_tile_glb_ranges`) now refuses that at sim start. Each IO tile gets one GLB bank
      (inputs bank 2·tile, outputs 2·tile+1); IO tiles in the plain layout whose byte ranges
      overlap, or run past the GLB, give "ERROR: GLB: ... overlaps ..." and exit(1). The
      E64 / multi-bank / MU-tiling / bank-toggle / GLB-tiling / padding layouts are not checked.
      Wide data needs a bigger `--glb_tile_mem_size`.
  - **Not width-related:** `tests/mem_{filter,slice,transpose}_test` fail on a lake-spec MEM at
    dw16 too (OPEN_ISSUES cross-repo/spec-mem-unit-tests). dw64 fw4 specs have no SRAM macro,
    so garnet fails "No valid macros"; use fw2 at dw64.
  - **Arithmetic width:** compute runs at the fabric width, so an app relying on 16-bit
    wraparound gives different results at other widths.
- **What changed, per repo:**
  - Halide: `inst_bitwidth` plus buffer, C-model and data-file widths.
  - clockwork: `DATAPATH_WIDTH` from the collateral, plus IO/Mem widths.
  - MetaMapper: `data_width()`, `gen_PE_fc(W)` and header widths.
  - lassen: `scripts/widen_rewrite_rules.py`. It widened the 51 integer rewrite
    rules mechanically, and all 51 pass SMT verify against `gen_PE_fc(32)`.
  - garnet: netlist bus width, IO port renames and the app width check.
  - archipelago: the STA B17 fallback (31285ac; measured to hold, see archipelago/CLAUDE.md)
    and width-generic port/graph names (6d37530).
  - testbench: lanes = 64/dw.
  - aha: map/pnr/test plumbing (above).
  - lake: collateral `data_width`.
- **Default behaviour is unchanged:** at 16 (no spec, or a dw16 spec) the outputs match the
  stock toolchain, and Halide keeps its native widths.
- **Width is not a make dependency.** `make clean` the app when switching
  widths, or stale 16/32-bit artifacts get mixed.
- **Tests (2026-10-12):** `tests/test_data_width/test_data_width.py` (~5 min; 24 tests).
  - It builds a 4x2 fabric at dw 8/16/32/64 with `metamapper.data_width` hidden from garnet's
    own code (the stock-container case). It then checks MEM/PE/pond ports at dw+1, B1 + B{dw+1}
    switch boxes, `inst` = 36 + 3·dw, and the GLB header's `CGRA_DATA_WIDTH`.
  - `glb_ranges_test.c` (gcc, `#include`s `tests/test_app/lib/map.c`) checks
    `check_io_tile_glb_ranges`: fit / overlap / past-the-end / bank-toggle.
  - Also covered: `check_app_data_width`, the 16-bit fallback with an older MetaMapper, and the
    three container scripts fetching one lassen branch.
  - It runs garnet.py in the repo root like `tests/test_garnet`, with `GARNET_HOME` set to this
    checkout. Without that, garnet.py writes its GLB / GLC / MU headers into whatever
    `GARNET_HOME` the shell has; on 2026-10-12 that overwrote the shared /aha/garnet's.
  - End to end: aha `tests/test_data_width_e2e.py` (opt-in, private tree).
- **Container garnet build: `common/rtl/garnet_build.sh` (2026-10-16, session 1fa8a391).** The rtl
  step used to run `aha garnet <flags>` (aha's retry: up to 3 runs on SIGSEGV/SIGBUS/SIGABRT, no
  timeout). On the build machine (2026-10-14, the RV pipeclean) garnet.py printed `- garnet.py DONE`,
  then died at exit with `double free or corruption (out)` (SIGABRT, the native kratos/coreir heap
  corruption). aha retried the finished build, and the retry hung mid-generation for 14 hours.
  gen_rtl.sh now runs garnet_build.sh (copied in with garnet; falls back to `aha garnet` without it):
  python garnet.py up to 3 times, each under `timeout` (`GARNET_BUILD_TIMEOUT`, default 7200 s; a
  4x2 build takes ~2 min). An attempt that printed DONE and wrote `garnet.v` counts even if it then
  died: garnet.py prints DONE after `build_verilog`. Tests: `tests/test_mflowgen/test_garnet_build.py`
  (stub python: ok / DONE-then-abort / abort / hang / DONE without garnet.v). Not run in the real
  container here (no docker on /aha).
- **Container steps (build machine), fixed 2026-10-12 (garnet 69f236e0, 84621c08).** `common/rtl/gen_rtl.sh`,
  `common/memtile-power-test-gen/run.sh` and `common/application/run.sh` run garnet.py in
  `stanfordaha/garnet:latest`, which has aha master's lassen (d2a4411) and MetaMapper (a6fe971).
  Only host garnet and lake are copied in. From e30c6792 until this fix, garnet imported lassen
  `gen_PE_fc` and `metamapper.data_width` at construction, so every container step failed with
  `ImportError: cannot import name 'gen_PE_fc'`, at dw16 too. Both live only on our personal
  branches (lassen and MetaMapper `thesis`). Now:
  - The three steps check out lassen `thesis` (aha mek's lassen) in the container. It's fetched
    from `https://github.com/StanfordAHA/lassen.git` into a fresh bare repo
    (`/tmp/lassen_cdw.git`, `GIT_TERMINAL_PROMPT=0`), then from that path into /aha/lassen,
    with `checkout -f -B thesis FETCH_HEAD`. On failure they print the remote and the git-config
    key names. The branch is a strict superset of d2a4411; at 16 bits it builds the same PE.
  - **Why a bare repo** (1fa8a391, 84621c08). The image's /aha/lassen git config carries a stale
    GitHub auth header (`http.<url>.extraheader`). Any github.com fetch from that repo gets a 401,
    which shows up as "could not read Username for 'https://github.com'". That happens with
    `origin` (69f236e0) and with an explicit URL (e650254f) alike, although the remote is public
    and anonymous fetches work in the container. A fresh bare repo has no such config. Lake's
    `origin` fetch works because lake is docker-cp'd from the host.
  - **Rerunning an existing workspace needs `--clean rtl`**: mflowgen doesn't re-copy a step's
    scripts, so an old workspace keeps the old fetch.
  - The branch was `cgra-data-width` until 2026-10-12, then `thesis` (user: personal branches
    named `thesis` for repos outside clockwork/lake/garnet). Both point at 52f023e today.
  - MetaMapper is not switched: its `thesis` is based on mek's a34e725, which lacks three of
    a6fe971's commits (84-bit inst schema, node sort). Instead RTL generation no longer imports
    MetaMapper's `data_width` (see "PnR" above), and `mapper/netlist_util.py` falls back to 16
    when MetaMapper lacks it. Mapping at another width with such a MetaMapper raises a clear
    ImportError, so the legacy application path (no `--app-bundle-dir`) maps at 16 only.
  - **Checked locally** with the image's pins (lassen d2a4411 → 52f023e, MetaMapper a6fe971,
    canal 4e6f931): 4x2 builds at dw16 and dw32 with gen_rtl's flags. The dw16 garnet.v is
    byte-identical to the mek-pinned build (`PYTHONHASHSEED=0`). Scratchpad
    `a16b3973-.../scratchpad/dwp/ctr/`.
    - Those checks never used the image's git config, which is why the auth header was missed.
    - The bare-repo fetch of `thesis` was then checked on a clone with a fake `extraheader` and
      an edited tracked file: it checks out 52f023e.
    - Without docker here, only the build machine runs the container itself.
  - Once lassen's branch is merged to master and aha master's image is rebuilt, the lassen
    checkout lines can go.
- **dw 8/32/64 Tile_MemCore PPA (gf12, done 2026-10-14: all 24 synthesized, 6 through PnR).** The thesis set has 24
  configs at these widths (18 static, 6 RV; 12 RV skipped for fw>1 and vc>2). The user's choice
  (2026-10-13): synthesis only, with PnR projected through the dw16 run's synth→PnR fit.

      ./mflowgen/sweep_specs.py --spec-set thesis --data-width 8,32,64 \
          --runtime-mode static,rv --flatten-effort 0 --memtile-power \
          --stop-after cadence-genus-synthesis --config-jobs 4 --zip \
          --out-dir /sim/mstrange/BUILD_CGRA/sweep_out/tile_memcore_dw8_32_64

  - **`--stop-after cadence-genus-synthesis` is required for synthesis-only.** Without it (or
    without `--pnr-set`) every config defaults to `synopsys-pt-timing-signoff`, i.e. full PnR.
    `--synth-stop` only applies to configs outside a given `--pnr-set`.
  - Dry run: 24 configs → `cadence-genus-synthesis memtile-power-synth-idle
    memtile-power-synth-active`.
  - A synthesis-only out-dir has no PnR rows, so its `correlation.csv` has no projections. Apply
    the dw16 run's `correlation_fit.csv` (`/aha/sweep_out/dw16_NEW_SWEEP_20261009/`) to the synth
    numbers instead. Check the `_proj_extrapolated` idea by hand: dw64 / fw8 tiles may sit outside
    the dw16 fit's synth range.

  The build machine's garnet must be at 84621c08 or later, and existing workspaces need `--clean rtl`. Pre-checked on /aha 2026-10-12 in the
  image-like environment above, with gen_rtl's exact garnet.py flags:
  - All 24 build tile RTL on the first attempt.
  - Each has exactly one SRAM macro family, and `get_macro_name.find_macro_name` returns it:
    W04096B008 (fw2 dw8), W02048B016 (fw4 dw8), W01024B032 (fw8 dw8, fw2 dw32) and W00512B064
    (fw4 dw32, fw2 dw64).
  - MEM pins are `MEM_{input,output}_width_{dw+1}`, and the switch boxes are B1 + B{dw+1}.
  - memtile-power-test-gen runs for fw4 dw32 static + RV.
  - Scratchpad `a16b3973-.../scratchpad/dwp/ppa/` (`check24.py`, `check24.txt`).
  - **Result (zips `tile_memcore_dw8_32_64_r8cad-gf12_20261014-190943` and
    `tile_memcore_dw8_rerun_r8cad-gf12_20261014-232023`; analysis in
    `/aha/sweep_out/dw8_32_64_SWEEP_20261014/README.md`):**
    - **All 24 PASS.** Synth timing is met everywhere, with one macro family each, and all power
      sims PASS on B9/B33/B65 tracks.
    - The 6 dw8 configs first failed in the RTL step: their workspaces predated 84621c08 and kept
      the old lassen fetch. They were rerun in a fresh out-dir under `/nsim/mstrange/BUILDS`.
    - 6 went through PnR + PT + PnR power: fw4 dw8 / fw4 dw32 / fw2 dw64 vc2, static + RV. PT setup
      WNS was −4…−19 ps at dw8, the same scale as the dw16 PnR tiles.
    - **Projection across widths:** `--correlate-only` over a dir symlinking the dw16 run's
      workspaces plus these, with `--validate-set dw16_val4,<the 6 new PnR configs>`, keeps the
      dw16 fit exactly. The 6 held-out PnR tiles:
      - total area within 2.3% (dw8 +0.3 / −0.7%; dw64 −1.2 / −2.3%);
      - power within 8%, except dw8 RV idle (+11.7%) and active (+6.9%).
    - Power has a width trend: PnR comes out below the projection at dw8 and above it at dw64.
      Adding the 6 points to the fit doesn't remove it (dw8 RV idle residual still 12%) and worsens
      the dw16 held-out area. So the dw16 fit stays the projection, with that spread.

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

## Lint: pycodestyle / flake8 (2026-10-13/14, session 352df910)

- garnet's own checks: `setup.cfg` `[pycodestyle]` (max line 140, ignores E501 and
  others) and `bin/lint.sh` (Buildkite `ci.yml`, `soft_fail`: autoflake duplicate keys,
  flake8 E and F with `[flake8]`, which does NOT ignore E501). Neither tool is in /aha's
  venv: `pip install --target <dir> pycodestyle flake8 autoflake`, then
  `PYTHONPATH=<dir> python -m pycodestyle <files>`.
- **All tracked `.py` files pass `[pycodestyle]` since 2026-10-14** (pycodestyle 2.12;
  1,737 violations fixed, mostly upstream code). `tests/test_style/test_python_files.py`
  keeps it that way: every tracked file compiles (push_button_sweep_all.py did not) and
  pycodestyle passes; skipped without pycodestyle, which `.github/scripts/run_pytest.sh`
  now installs. Unfixable-without-risk spots carry `# noqa`: `== True/False` (E712; the
  value may not be a bool), an E402 after `matplotlib.use`, two kratos `@always_comb`
  conditions (E124). `== None` (E711) and `type(x) == T` (E721) became `is` where the
  operands are plain Python values. flake8 F (pyflakes) findings are not addressed.
- `tests/test_mflowgen/test_construct_graphs.py` builds every mflowgen design's Graph
  (stub gf12 ADK + stub `calibre` on PATH; `common/tile-post-*-power` get
  `clock_period`/`design_name` from the env).
- **CI on modern_gf (2026-10-15, session 352df910).** GitHub `pytest` and `verilator`
  run modern_gf in the stock `stanfordaha/garnet:latest` container (aha master's pins),
  so they died at import (`cannot import name 'gen_PE_fc'`, every push since at least
  2026-10). `.github/scripts/aha_mek_deps.sh` now runs in the container first: it reads
  aha `mek`'s gitlinks and checks out those commits in the editable Python repos (lake,
  lassen, canal, archipelago, MetaMapper, mflowgen) plus mek's Halide-to-Hardware
  `apps/hardware_benchmarks/hw_support` (copied in; the image's H2H is not a git repo).
  Compiled code (coreir, clockwork, Halide's C++) stays as the image built it.
  - pytest.yml runs it after copying garnet in; `run_pytest.sh` installs pycodestyle
    and marks /aha/garnet a git safe.directory (the image's git ignores `-c` for that),
    so tests/test_style runs: 63 passed, 21 skipped (the same skips as on /aha).
  - verilator.yml passes it to `tests/test_app/test_app.sh` as `AHA_DEPS_SCRIPT`
    (unset = unchanged), which builds a 4x2 CGRA, maps/PnRs/runs tests/fp_pointwise:
    passes. Both workflows also start by hand (workflow_dispatch: `POST
    /repos/StanfordAHA/garnet/actions/workflows/<file>/dispatches {"ref": "modern_gf"}`).
  - A commit with `skip ci` in its message skips both GitHub workflows and the Buildkite
    builds; a dispatched run still runs.
  - Buildkite `garnet` (.buildkite/ci.yml) skips its `aha regress pr` step on modern_gf
    (`if: build.branch != "modern_gf"`, user decision 2026-10-15): in the stock container
    it needs mek's compiled clockwork/Halide too, and failed on every push. Since
    79c22022 (2026-10-17) it also skips "Get latest docker" and Lint (soft_fail) there:
    the pull of the ~9 GB image failed on the agents' full docker disk (6417, 6418), and
    the image only fed Lint. Only "Delete container" (all `|| true`) runs on modern_gf.
    Buildkite logs: API token at ~/.config/buildkite/token (read endpoints only).
