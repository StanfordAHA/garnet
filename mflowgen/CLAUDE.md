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
- `--recipe <name>` — named parts of the thesis data set; see "Thesis data recipe" below.
- `--spec-set {default,thesis,filter_fifo,clock_gating,thesis_*}` — `default` = the 6 `DEFAULT_SPEC_POINTS`;
  `filter_fifo` = the conv_3_3 A/B spec (RV, `_ff8`; see "Whole-CGRA power of
  app variants"); `clock_gating` = the clock-gating A/B (below); `thesis_*` = the thesis
  fabrics ("Thesis fabrics");
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
- `--rtl-only` — stop after the RTL step (fast; runs locally, see below). With
  `--memtile-power` (2026-10-19) it also makes `memtile-power-test-gen`. Those are the
  graph's only two docker steps, and they run on the full run's graph and settings. The same
  command without `--rtl-only` then builds to the end without docker: make finds both steps
  built. That matters because the build machine's `/sim/docker` filled up partway through
  two long runs (2026-10-18 and 10-19) and failed every later container step at `docker run`.
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
- Reports in the zip (2026-10-18): besides the PPA subset (`ARTIFACT_GLOBS`, also
  copied to `artifacts/`), `REPORT_ZIP_GLOBS` puts every Innovus step's `reports/`
  (timeDesign's per-group `*.tarpt` path reports, place/cts/route reports) and every
  Genus report (`reports/`, `results_syn/*.rpt`) in the zip only; a file over
  `REPORT_ZIP_MAX` (32 MB) is left out and named. cgra_app_power.py's zip has every
  synthesis report too.
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

### Thesis data recipe: `--recipe` (2026-10-17; stock-fabric parts removed 2026-10-24)

`--recipe <name>` runs named parts, each its own sweep into `<out-dir>/<part>` with its own
CSVs and zip (`<out-dir>/<part>_<host>_<ts>[_slim].zip`). The flags are the part's
`RECIPE_FLAGS`, then the command line's, which override them: a top-level `--clock-mhz`
re-clocks every part. A failed part does not stop the rest.

- **Thesis results come from the thesis fabrics** (user, 2026-10-20): `thesis_fmax` →
  `thesis_tiles` → `thesis_dse_reduced` / `thesis_dse` with `--clocks-from`, then
  `cgra_app_power.py` over the thesis bundle sets. See "Thesis fabrics" and "Thesis
  design-space sweep" below, and "Thesis whole-CGRA power set" for the bundles.
- **`--recipe thesis` = `memtile` + `app_power`, on garnet's stock fabric.** That is the data
  behind the thesis figures today, whose "static" tiles are the RV + sparse fabric with its
  FIFOs bypassed.

  | Part | Graph, clock | Configs | Builds |
  |---|---|---|---|
  | `memtile` | Tile_MemCore, 750 MHz | `--spec-set thesis` at every data width: 196 configs | PnR: preset `memtile_pnr` = `dw16_pnr12` + `dw8_32_64`; held out: `dw16_val4` + `dw8_32_64` (the fit is the 8 dw16 points); idle/active power |
  | `app_power` | `cgra_app_power.py --any-config`, 400 MHz | each `<app>` under `--app-bundles` is a variant | synth-level app power |

- **Removed 2026-10-24: `fabric_mem`, `pe_tile`, spec sets `fabric` / `pe_tile`, preset
  `pe_tile_pnr`, the `fabric` knob and the rtl param `dense_only`.**
  - They built a static fabric through `garnet.py --dense-only`, which crashes at HEAD and
    ignores the lake spec.
  - They built stock PE tiles. `thesis_tiles_pe` and `thesis_fabric` build the PE and
    switch-box comparison on the fabrics the thesis compares.
- **Tile knobs still there** (sweep-only config keys, `SWEEP_ONLY_KEYS`):
  - `stock: True` = no `LAKE_SPEC_CONFIG` (garnet's stock tile; name `stock`);
  - `pond`: `none` sets `NO_POND`; `spec` sets `LAKE_POND_SPEC_CONFIG` to
    `<ws>/pond_spec.json` = `{}`, lake's default spec pond. Names get `_nopond` / `_specpond`.
  - Both are exported only when set and recorded in `sweep_meta.json` with the graph.
    correlation.csv / memtile_power.csv get those columns only when a workspace has them.
- **Tile_PE clock.** Tile_PE reads env `clock_period_PE` (default 1.1 ns), not
  `CLOCK_PERIOD`, so `--clock-mhz` goes there for Tile_PE (`_clock_env_key`).
- **Stale-step check** (`_off_param_change`). A parameter only one side has, and off
  (`False` or empty) on that side, is not a change: an opt-in knob added after a step ran,
  or one removed since (`dense_only`, exported as `False` by every rtl step from
  2026-10-17 to 2026-10-24). So neither fails resumed workspaces.
- **Lake ingest.** lake `THESIS/pipeline/tile_sweep.py` ingests memtile zips, and (2026-10-25)
  `python3 -m THESIS.apps.cgra_power_ingest` turns a `cgra_app_power.py` zip into the Ch. 5 app
  figures' `results.json` (lake `THESIS/apps/CGRA_APP_POWER.md`: the bundle matrix and commands,
  `python3 -m THESIS.apps.garnet_configs --commands`). Nothing in lake reads the thesis-fabric
  tile zips yet.

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

Lake 9f9480c9 adds two Spec power options. They were opt-in until 2026-10-28; they are lake's
default since then. Sweep configs still write them explicitly, so a config name without
`_sharectr`/`_portcg` stays ungated (`POWER_OPTION_KEYS` in sweep_specs.py; details below
the A/B results):
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

**First gf12 run (2026-10-17/18; zip
`/aha/clock_gating_ab_20261017_r8cad-gf12_20261018-022542.zip`, extracted in
`/aha/sweep_out/clock_gating_ab_20261017/`; lake CLAUDE.md §5.6 has the table).** 5 of 6 PASS.
- Static, 750 MHz, tile power, synth -> PnR:
  - shared counter: idle -36% / -27%, active -5% / -5%; PnR logic area -3.6%;
  - port gating: idle -56% / -44%; active unchanged at synth, +1% at PnR (the
    clock-tree cells after the gates);
  - both: idle -56% / -42%, active -6% / -4%.
- RV base was `Killed` in Innovus postroute: about 8 GB with six PnRs at once,
  likely OOM.
- RV gated failed timing (synth -99 ps, PT -82 ps). Static gated was -1 ps on
  reset. The gates captured their enable on the falling edge, and the tile's
  `reset`/`flush` inputs arrive at `pt_i_delay` 0.7 ns, after the 0.667 ns
  falling edge.
- Fixed in lake 2660629d: `gclk = clk | ~config_bit`, with no falling-edge logic.
  It is verified locally: gold sims, suites, the gated tile tests and RV
  conv_3_3 bit-accurate.

Re-run: all six, fresh, into a new out-dir. Since garnet 6f110058, `--no-pd` works, so
PWR_AWARE False tile builds have no power-domain logic and the first run's tiles (with it)
aren't comparable with new ones. This needs `/sim/docker` freed first (see "dw 8/32/64
all-PnR", first run) and at most four PnRs at once (OOM):

    ./mflowgen/sweep_specs.py --spec-set clock_gating --flatten-effort 0 \
        --memtile-power --config-jobs 4 --fresh --zip --zip-slim \
        --out-dir /nsim/mstrange/BUILDS/sweep_out/clock_gating_ab_20261018

**Second run (2026-10-18/19; zip `/aha/clock_gating_ab_20261018_r8cad-gf12_20261019-041557_slim.zip`,
extracted in `/aha/sweep_out/clock_gating_ab_20261018/`; table in lake CLAUDE.md §5.6).**
All six built through PT signoff at lake 2660629d. Synth WNS is 0 everywhere, the RV
gated tile included. PT WNS is -6 to -23 ps, all on pass-through feedthroughs. Static,
synth / PnR:
- shared counter: idle -35% / -26%, active -5% / -5%, logic area -3.8%;
- port gating: idle -59% / -48%, active 0% / 0%;
- both: idle -59% / -46%, active -6% / -4%.

The two RV configs' power steps failed: `/sim/docker` was full again at
memtile-power-test-gen's `docker run`. Their builds are done, so a power-only re-run on
the existing workspaces finishes them. Free `/sim/docker` first (kill leftover
`gen_rtl_*`/`memtile_power_*`/`mstrange-*` containers). No `--fresh`: `--skip-existing`
makes only the missing power leaves, and `--reuse-graph` keeps each workspace's graph if
garnet was pulled since. The test generator rebuilds the spec from lake origin/THESIS,
so run it before any lake spec change (the RTL is lake 2660629d):

    ./mflowgen/sweep_specs.py --spec-set clock_gating --flatten-effort 0 \
        --memtile-power --config-jobs 2 --skip-existing --reuse-graph --zip --zip-slim \
        --only fw4_dw16_sc4096_sp_in2_out2_vc2_rv,fw4_dw16_sc4096_sp_in2_out2_vc2_portcg_rv \
        --out-dir /nsim/mstrange/BUILDS/sweep_out/clock_gating_ab_20261018

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
  **Edge-pin fit (2026-10-28, session 43d74890; Tile_PE's floorplan.tcl too).**
  pin-assignments.tcl spreads the SB pins one per track: left/right on routing
  layer 6 (gf12 K1, 0.128 um, horizontal) over the halves of [5, die_h - 15],
  top/bottom on layer 5 (C5, 0.080) over [5, die_w - 5] (MemCore: split SB /
  config). At the fixed 226 rows a half holds 341 tracks; an RV dw64 tile has
  345 pins per half (5 x 66 + 15), so thesis_dse's RV dw64 fit tile (smallest
  dw64 SRAM, no SRAM grow) failed init with IMPPTN-970 on the LEFT side
  (height, not width), and the RV dw64 PE tile of thesis_tiles_pe would too.
  A second self-gated branch now grows height (even rows) or width when a
  side's pins don't fit, with 2 tracks of slack; the pitch comes from the
  routing layer by index (`num`), as editPin reads `-layer M6` (gf12 has no
  layer named M6). Checked against all 55 gf12 MemCore init logs in
  /aha/sweep_out (thesis_dse, thesis_mem, thesis_opt, memtile_pnr x2): only
  the failing tile changes (226 -> 230 rows); every passing tile keeps >= 3.7
  um of height and >= 27.9 um of width margin. freepdk45 harness (Innovus
  23.1, MemCore + PE scripts; scratchpad 43d74890 `pinfit/`): pins that fit
  give the same die; 540 pins per half or a narrow die fail IMPPTN-970 without
  the branch and pass with it.
- **`common/init-scripts/fix-tap-gaps.tcl`** (linked from `Tile_MemCore/` and, since
  2026-10-29, `Tile_PE/custom-init/outputs/`; thesis Tile_PE in the next bullet) — lake-spec builds
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
- **Thesis Tile_PE runs fix-tap-gaps.tcl too (2026-10-29, session bc48e85f).** The static dw64
  thesis PE tile (`fw2_dw64_sc8192_sp_in2_out2_vc2_sharectr_portcg_thesis`, 142.272 um die) failed
  route with NRIG-76: CTS's checkPlace found 113 filler-gap violations (about one per alternate
  row, the row-end pattern), and its seven siblings at other widths and dies found none. Tile_PE
  construct.py adds the script to custom-init's outputs and to init's `order` right after the
  well-tap script when `THESIS_FABRIC` is set (pd variant when pwr_aware), so garnet's own PE graph
  is unchanged. Test `test_fix_tap_gaps_after_the_well_taps`; a materialized thesis graph's
  custom-init step holds the dereferenced script. Not yet re-run on gf12: the next build of that
  tile (now named `fw4_dw64_sc16384_...`, the same PE tile since d5489e0d) is the check.
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
  **PnR level = SDF sim with SDC-timed inputs (2026-10-28, session 43d74890;
  garnet/pnr-power-sim-no-sdf-race).** It used to run the post-CTS signoff
  netlist on the cell models' specify delays only (`-notimingchecks`), with
  every input driven 0.2 T after the edge. In thesis_dse (1.493 ns, thesis SDC
  `pt_i_delay` 0.25 T = 0.373 ns) that put config/reset/flush 75 ps before the
  arrival PnR fixed hold for, and one RV output port of 2 of 37 tiles never
  moved (fw4 dw8 sc8192 in2/out2 T1, fw8 dw32 sc16384 in4/out4 T2; synth level
  fine). Same failure class the app replays fixed on gf12 (run 3 -> run 4,
  "Bundle guards"). Now Tile_MemCore wires signoff's `design.sdf` into the two
  pnr sims (`extend_inputs`), and run_sim.sh, when `inputs/design.sdf` exists:
  annotates it at `testbench.dut` (MAXIMUM, `-negdelay`), keeps timing checks
  with `-nonotifier` instead of `-notimingchecks` (as cadence-xcelium-sim), and
  passes `+define+IN_DELAY` / `PT_IN_DELAY` = the SDC's i_delay / pt_i_delay
  (0.2 T / 0.7 ns, or env TILE_I_DELAY_NS / PT_I_DELAY_FRAC like
  constraints/common.tcl). The generated testbench drives reset, config and
  flush at DPT (`PT_IN_DELAY`) and the switch-box inputs at D (`IN_DELAY`);
  without the defines both are 0.2 T, so the synth level keeps its inputs and
  arguments. Tests `tests/test_mflowgen/test_memtile_power.py` (tb timing, the
  sim's args with/without SDF, SDC constants vs common.tcl) and
  `test_construct_graphs.py::test_memtile_power_pnr_sims_get_the_signoff_sdf`.
  Checked on /aha (scratchpad 43d74890 `psdf/`): the failing tile's spec
  (`fw4_dw8_sc8192_sp_in2_out2_vc2_nofp_portcg_thesis_rv`, `--use_sim_sram`)
  RTL active 973/974 changes (= gf12 synth level), idle PASS, with and without
  the defines; Genus freepdk45 netlist + SDF through the real run_sim.sh: no
  SDF / SDF (onyx delays) / SDF (thesis delays) active PASS 973/974, idle PASS,
  path delays 100% annotated, 0 annotation errors, 0 timing violations. The
  gf12 race itself can't be reproduced here (no gf12 netlist or ADK): first
  check on the build machine is those two tiles' pnr-active sims.
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
Make `MetaMapper` and `clockwork` real directories in it too, with symlinked contents and
real copies of their `*_header.json` files. hw_support `make map` copies the app's headers to
`$(CLOCKWORK_PATH)/` and `$(METAMAPPER_PATH)/../garnet/headers/`. Through symlinks those land
in the shared /aha (`..` of a symlinked dir is its real parent, and `cp` onto a symlink writes
its target). At dw16 that is harmless (same content as HEAD), but on 2026-10-22 a16b3973's
dw 8/32/64 runs put other widths' headers there for about 20 minutes. Template: scratchpad
a16b3973 `thesis_dw/make_tree.sh`.
A real MetaMapper dir is not enough when Halide-to-Hardware is a link to /aha. `METAMAPPER_PATH`
defaults to `$(CLOCKWORK_DIR)/../MetaMapper`, and `CLOCKWORK_DIR` to a path derived from
hw_support's real location (`/aha/clockwork`), so the garnet copy still went to /aha/garnet/headers.
aha exports only `CLOCKWORK_PATH`, which is why the clockwork copy stayed private. On 2026-10-28
the thesis dw32 re-runs left 32-bit io/lassen/mem headers in the shared garnet (restored).
gen_app_bundle.py now exports `METAMAPPER_PATH=<tree>/MetaMapper` for any `--aha-dir` other than
/aha (`private_tree_env`), and stops if that MetaMapper is a symlink. Checked: `aha map` in such a
tree writes `<tree>/garnet/headers` and leaves /aha/garnet's untouched. aha's
tests/test_data_width_e2e.py does the same since 2026-10-28 (a16b3973). Any other private-tree
flow with Halide-to-Hardware linked to /aha needs it too.
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

**Thesis whole-CGRA power set (2026-10-23, session 1fa8a391): the set to use.**
`/aha/sweep_out/app_bundles_thesis_power_20261023` (+ .tgz, STATUS.txt), 16x16 thesis, dw16, lake THESIS
ca947229 snapshot. User's tiles: static `fw4_dw16_sc4096_sp_in2_out2_vc2_sharectr_portcg_thesis`, RV
`..._nofp_portcg_thesis_rv` (FIFO-8 dropped): conv/gauss/harris/mmpond on both (garnet c9c6da9b; the PE pond
inherits the MEM spec's gating, so bundles from before lake ca947229 fail check_bundle on the new Tile_PE).
Filter-path A/B (user request via cfc4174c): on `..._ff8_portcg_thesis_rv`, conv (A) + gauss as compiled and
`convB` (hooks/conv_3_3_eat_rows_up_front.py, METAMAPPER_MEM_PORTS=3; garnet ddf1c53b; it does not apply
to gaussian, whose line buffer is banked over several MEMs). All bit-accurate; B = A's 4150 ns and 3844
outputs, but 14 MEM / 38 PE tiles vs 9 / 25. One run: `cgra_app_power.py --any-config --variants
conv=..,gauss=..,harris=..,mmpond=..,convB=.. --clocks-from <thesis_fmax dir> --replay-jobs 4` (dry run:
static 490, RV 570 MHz). Answers: static vs RV energy per frame; filter path always-on cost = conv/gauss on
ff8 minus nofp; B's saving = convB - conv on ff8. First-cut estimate (before gf12): B saves <= ~9.6 nJ per
frame per 3x3 stage (1220 fewer word reads x 2 x 3.93 pJ, TT macro datasheet; lake deselects the macro on idle
cycles, CEN = ~(re|we)); the ff8-vs-nofp idle delta (+29 uW synth / +70 uW PnR per MEM tile at 400 MHz) is
~99% dynamic in the tile wrapper's third-port FIFOs + CB/SB fan-in (cfc4174c), so x64 tiles is an upper bound
and it could be gated in garnet/canal.

**Thesis-fabric app-bundle set (2026-10-21, session 1fa8a391).** User direction (2026-10-20, via
cfc4174c): thesis results come from the thesis fabrics. conv_3_3, gaussian, harris_color and pond
matmul on 16x16 `garnet.py --thesis static|rv` CGRAs, lake's default thesis spec
(`fw4_dw16_sc4096_sp_in2_out2_vc2_thesis` / `_thesis_rv`, `--cgra-tiles`; static with the static
spec pond `--pond-spec {}`, RV with the RV spec pond and DENSE_READY_VALID only, so `aha pnr`
latency-balances). All 8 bit-accurate; kernel ns static / RV (RV padding registers): conv 4149 /
4150 (10), gauss 6389 / 6390 (26), harris 16772 / 16794 (508), mmpond 9260 / 13355 (0).
`/aha/sweep_out/app_bundles_thesis_20261022/<app>/<config>` (+ STATUS.txt, tarball
`app_bundles_thesis_20261022.tgz`). Recorded in private trees with a lake THESIS b01b1531 snapshot
on PYTHONPATH (runner: scratchpad 1fa8a391 `thesis/`): static on garnet b0e9ba87; RV re-recorded
2026-10-22 on garnet 8c2289f5 (canal 24db49a), after the thesis RV PE tile got its pond-input CB
FIFO (72977053; same tile ports, other RTL): same kernel ns and padding, new garnet.v. Power:
`cgra_app_power.py --variants conv=..,gauss=..,harris=..,mmpond=.. --clock-mhz 400`; tile_env gives
both tile graphs THESIS_FABRIC (checked).

**dw16 app-bundle set (2026-10-14/16, session 1fa8a391; user scope).** conv_3_3, gaussian,
harris_color and pond matmul (`tests/matmul_rvtry3` n=16, `-enable_ponds`) x the 12
`dw16_pnr12` configs, 16x16, `--cgra-tiles`, RV without `--rv-balance`; static bundles with a
static spec pond (`--pond-spec {}`, so one Tile_PE per config serves every app). Recorded in 6
private slot trees (garnet 495cf23f + the `--dual-port` fix, lake snapshot 11967ce5 on
PYTHONPATH; runner + logs: scratchpad 1fa8a391 `bigset/`). Result: 32 bundles over 10 configs,
8 per app, all `aha test` bit-accurate; `/aha/sweep_out/app_bundles_dw16_20261014/<app>/<config>`
(+ `STATUS.txt`, tarball `app_bundles_dw16_20261014.tgz`). 2026-10-18: + static pond matmul on
fw8 sc32768 and fw4 vc4, re-recorded with clockwork 038a82bc (Static TB capacity) and garnet
b6dfabb7, bit-accurate: 34 bundles; add-on tarball `app_bundles_dw16_20261018_mmpond_tbfix.tgz`
(extract into the unpacked set). Power: `cgra_app_power.py
--any-config --variants conv=..,gauss=..,harris=..,mmpond=.. --clock-mhz 400`.
First gf12 run (2026-10-17): the Tile_PE builds of the dual-port RV configs failed in the rtl
step (lake `resolve_memports` IndexError): an RV bundle's PE tile is built with the bundle's
lake spec, and Tile_PE's construct.py did not forward `DUAL_PORT`, so garnet.py built the
dual-port spec without `--dual-port`. Fixed: Tile_PE passes `dual_port` when it has a lake spec
(static PE tiles, built without one, are unchanged); test `test_tile_pe_rtl_dual_port`. Rerun
those workspaces with `--clean rtl`. The same run grew to 166 GB and filled the build disk:
every replayed tile (placed, route and idle, per variant) dumped a full-depth gate-level SHM
(`waves: True` in tile-post-*-power). Nothing reads it (power is from the SAIF, and
run_sim.sh's copy tests `true` so it never ran), so `waves` is now False there; env
`REPLAY_WAVES=True` turns it back on to debug a replay (test `test_replay_waves_off_by_default`).
The second run (2026-10-18/19, waves off) filled /sim again: each replayed tile's
sub-workspace (`<step>/Tile_X*`) kept its copies of the netlist and of its per-cycle test
vectors, its xcelium snapshot, SAIF and ptpx data, for 100+ tiles per app on a 16x16 array, and
the application step copied each bundle's run.vcd (harris: 650 MB) into every workspace. Now
run_all_tiles.py deletes a tile's sub-workspace after its reports and replay check are written,
keeping only `mflowgen-run.log` / `xrun.log` (what the CSVs and zips read; env
`REPLAY_KEEP_TILES=True` keeps all), and the application step links run.vcd (tests
`test_step_prunes_replayed_tiles`, `test_step_keeps_tiles_on_request`). What is left per
workspace and variant is the testbench step's `tile_tbs/` (every tile's vectors, read by all
power levels). Before the fix that run had finished fw1 x2, fw2 dp static (all apps) and fw2 dp
RV: every finished tile replayed exactly.
Comparing power across runs: tiles built on garnet >= 6f110058 have no power-domain logic
(`--no-pd` was a no-op before), so their power/area is not comparable with the 2026-10-14
pipeclean numbers or with a run that mixes garnet versions; check `garnet` in each workspace's
`run_meta.json`. The two fw1-sp static mmpond bundles replay a schedule with one dropped SRAM
read (see the fw1 bullet): flag them or leave them out.
Whole-CGRA power of the set, stock fabric (2026-10-23; zip
`/aha/cgra_app_power_dw16_r8cad-gf12_20261023-085057.zip`, CSVs + RESULTS.txt in
`/aha/sweep_out/cgra_app_power_dw16_20261023`): 10 configs x 4 apps (no static mmpond on fw4 vc4 / fw8),
400 MHz, every replayed tile exact (66 steps, 2943 tiles). App mW static / RV (fw4 sc8192 2x2): conv
17.5 / 18.6, gauss 43.9 / 31.9, harris 225.5 / 115.8, mmpond 11.0 / 5.2; but these RV bundles were recorded
without branch balancing, so RV runs far longer (harris 333 vs 62 us, gauss 50 vs 24 us) and its energy per
run is 2.6-2.8x static for harris: a throughput artifact, not the fabric (the thesis RV fabric balances).
Memory config moves app power a few %; SRAM power tracks port count (dual-port fw2 3.6 mW vs fw4 2.4 mW on
conv, harris 34 vs 23 mW). Workspaces span garnet 13732565 / 3b70f5bb / 8c2289f5 (all no-PD; thesis-only
changes between them).
Failures (OPEN_ISSUES ids):
- fw1 single-port STATIC line buffers (`clockwork/static-mem-bandwidth-unchecked`, closed
  2026-10-18): each row bank is written and read every cycle (stride 1, overlapping) = 2
  accesses/cycle on a 1-access SRAM; output was wrong (conv_3_3 all 3844 ~half of gold). Since
  clockwork b68af72f such compiles stop with "ERROR: static compile: ports ... access its SRAM in
  the same cycle" (clockwork/CLAUDE.md "Static fw1 SRAM port check"). Static pond matmul too, at
  `aha pnr`'s reschedule: one clash at cycle 258; its bundle passed because the dropped read was of
  a zero. These fw1-sp static bundles cannot be regenerated.
- fw1 single-port RV (`garnet/fw1-sp-rv-netlist`), every app incl. pond matmul: PnR KeyError in
  `mapper/netlist_util.py`. FIXED 2026-10-24 (session 43d74890; garnet `visited_register_pairs`, test
  `tests/test_netlist_util`): fw1 collaterals have load/store latency 1, so clockwork delays the output
  op's start (`stencil_valid` -> `write_start`) through a 1-bit `corebit.reg delay_reg_*`; dense RV
  removes that output valid path downstream of clockwork, leaving the register with no connections, and
  `FixInputsOutputAndPipeline` never visits it -> KeyError RegisterSource. The earlier patch (skip
  unvisited sources and sinks separately) then broke the pairing: IODag zips register sources with sinks
  by POSITION, so every later pair shifted and the output IO's last pipeline register (`..._write_0$reg1`)
  lost its ID (the "second" KeyError was this, not a separate bug). Dropping the pair as a whole fixes
  both. Bit-accurate on RTL (gen_app_bundle, 16x16): conv_3_3 8266 ns, gaussian 12760, pond matmul_rvtry3
  13381 on fw1_dw16_sc4096_sp_in1_out1_rv; conv_3_3 8273 on fw1_dw16_sc8192_sp_in2_out2_dim4_msw1024_rv.
  conv/gaussian/matmul static fw4 = 4149/6389/9260 ns, so the single-port line buffers run at about half
  rate (lake's RV arbiter shares the one SRAM port); the pond matmul is not SRAM-bound (13364 on fw4 RV).
- Static pond matmul on fw8 sc32768 and fw4 vc4 (`clockwork/static-matmul-wide-mem`): wrong
  output; RV passes. FIXED 2026-10-18 in clockwork `ubuffer.cpp` (038a82bc; see clockwork/CLAUDE.md
  "Static TB capacity"): both configs bit-accurate in a full-flow re-run (9260 ns); bundles re-recorded
  2026-10-18 by 1fa8a391 (app_bundles_dw16_20261018_mmpond_tbfix.tgz).
  Cause (2026-10-17, reproduces 256/256 sim values on both): the kernel MEM's
  TB is overrun. matmul reads `kernel(x, r)` with r fastest. The kernel MEM (fw8) fetches word
  (r, x/8) for r = 0..15 once per 8-lane word (`sram2tb_0` start 512, strides [2, 272, 544],
  extents [16, 2, 16]). `tb2out_0` (start 515, strides [2, 34, 544], extents [16, 16, 16]) reads
  lane 0 right after each fetch, but lanes 1..7 only 34+ cycles later, when the TB holds only
  the last fetched row. So the hardware uses kernel row 15 for every r in lanes x % 8 != 0
  (x % 4 on fw4 vc4); lane 0 is right. Clockwork schedules as if the TB held 16 words, not
  vec_capacity. Same family as `clockwork/static-tb-fetch-war` (TB slot reused before its last
  read). An earlier note here said "every wrong value = gold + 7824"; that was wrong. Not pond
  packing: the mismatches are identical with garnet b6dfabb7. Analysis scripts: scratchpad
  1fa8a391 `packfix_ana/` (gold/sim arrays in the app's `bin/*.npy`).
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
  False`), `gen_app_bundle.py` does not. Until 2026-10-18 `--no-pd` was a no-op
  (a trailing-comma tuple in `cgra/util_onyx.py`, garnet/no-pd-tuple), so every
  tile build and every number above has power domains (per tile a
  `PowerDomainConfigReg`, CB muxes with a constant input, RV SB readies ANDed
  with the SB enable, the read_config_data OR). Since the fix, `--no-pd` tiles
  have none of that. Bundles recorded with power domains still fit them:
  `tests/test_cc_args` checks that tile ports and every other config register
  (feature index, name, width) are the same with and without, and app
  bitstreams never write the PD register. Tile area/power from before and
  after the fix are not directly comparable.

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
- Thesis power tiles match the thesis tile set (2026-10-22, session 1fa8a391): for a thesis
  bundle, tile_env exports TILE_I_DELAY_NS = sweep_specs.THESIS_I_DELAY_NS (0.23) and
  PT_I_DELAY_FRAC = 0.25 (the thesis recipes'; tile SDCs and generate_testbench read both;
  `--i-delay-ns` / `--pt-i-delay-frac` override), and `--clocks-from <thesis_clocks.json | thesis_fmax
  out dir>` clocks each thesis fabric at its own (mode, data width) clock, read with
  sweep_specs._thesis_clock_table; stock bundles keep --clock-mhz. run_meta.json records the clock.
  `--pe-registered-operands` (2026-10-26, session bc48e85f) gives a static thesis Tile_PE the
  thesis_tiles_pe constraints (PE_OPERANDS_REGISTERED=1, TILE_O_DELAY_NS 0.24); pass it whenever
  the tile set and its clock table used registered operands (thesis_tiles_pe always does, and
  `--clocks-from <dir>` takes the regops static PE limit when thesis_fmax_pe_regops is there).
- Parallel tile replays (2026-10-22, session 1fa8a391): each post-*-power step replays its tiles one
  after another (~4 min per tile on gf12; a 16x16 harris variant has ~175-230 tiles, so a PE
  workspace took 12-15 h). `cgra_app_power.py --replay-jobs N` (env `REPLAY_TILE_JOBS`, also
  honoured by sweep_specs runs when exported) runs N tiles at once; app-replay xrun gets
  `-licqueue` and PrimeTime `SNPSLMD_QUEUE=true`, so they wait for a license instead of failing.
  Load multiplies: tile-jobs x parallel-jobs (variants) x N sims.
  Verified on /aha (2026-10-22; scratchpad 1fa8a391 `tilepower/par_verify.sh`: run_local.sh's
  freepdk45 chain with the real step scripts, the thesis conv_3_3 bundle's 26 PE tiles): N=4
  9 min 50 s vs N=1 34 min 56 s (3.6x on a loaded 24-core machine), 26/26 exact both ways, every
  .hier/.cell/.replay.json identical apart from date lines, every replay xrun with -licqueue.
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
- **Kernel window, kernel stats, SRAM activity (2026-10-25, lake session 46a3d46c, for the Ch. 5
  app figures).** Before, the SAIF window ran from the stall release to `$finish`, which
  includes the testbench reading the output back from the GLB, and nothing recorded the
  kernel's cycles, output count or how busy each MEM tile's SRAM was.
  - `gen_app_bundle.py` writes manifest `kernel` = {kernel_ns, start_ns, end_ns,
    clk_period_ns, cycles, output_bytes, output_words, n_kernels}. They come from
    `logs/test.log` (tb `Env_kernel_test`: "kernel start at", "It takes ... total time to
    run kernel", "The size of output is ... Byte"; words = bytes >> cgra_byte_offset, the
    tb clock from CLK_PERIOD, default 1 ns).
  - It also writes `mem_activity` = per MEM tile {clk_edges, sram_read_cycles,
    sram_write_cycles, sram_access_cycles, memory_ports}. These are the rising edges of
    the lake controller's clk in [start_ns, end_ns) at which its
    `memory_port_{read,write}_en_out_*` ports (core.vcd) request the SRAM, sampled before
    the edge (lake drives CEN = ~(re | we)). The replay is checked exact against the
    recording, so these are the replayed tile's accesses too. A tile without such ports
    gets None.
  - `gen_app_bundle.py --annotate <bundle> ...` adds both to bundles recorded before.
  - `generate_testbench.py`: with manifest `kernel`, `saif_window` also falls
    `kernel.cycles` vectors after it rises (`app_window_end`, clamped below
    NUM_TEST_VECTORS). `saif_window_closes` tells cmd.tcl to stop on it, end the SAIF
    (`dumpsaif -end`) and run on to `$finish` for the replay check. Vectors are
    simvisdbutil rows, about one per recorded cycle, so the end can sit a few cycles
    off. Without `kernel` nothing changes.
  - `cgra_app_power.py`: `replay_window` ends at that stop when it fired.
    - `cgra_power_tiles.csv` gains `window_kernel`, `sram_access_cycles` and
      `sram_busy_frac` (= access / kernel cycles).
    - `cgra_power.csv` gains `window_is_kernel` (then `app_W` is the kernel average and
      `app_J` the kernel energy), `kernel_cycles`, `output_words`, `kernel_s` (cycles at
      the run's clock), `kernel_J` (= app_W x kernel_s) and `mem_sram_busy_frac` (mean
      over placed MEM tiles; None unless every one has activity).
  - Not run on /aha or the build machine yet. Tests: test_cgra_app_power.py
    `test_kernel_stats_from_the_test_log`, `test_sram_activity_counts_enables_before_each_edge`,
    `test_annotate_adds_kernel_and_activity`, `test_kernel_window_and_utilization_columns`;
    test_app_bundle_guards.py `test_testbench_saif_window_closes_at_the_kernel_end`.
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

**Default for every RV compilation since 2026-10-25 (user direction; session 43d74890).**
gen_app_bundle.py runs RV PnR without EXHAUSTIVE_PIPE on every fabric (`RV_PNR_ENV` =
`DENSE_READY_VALID=1` only), so `aha pnr` latency-matches the joins itself
(aha/util/rv_balance.py) and `aha test` starts balanced apps flush-first; the loop below runs
only with `--rv-balance N`, which brings back EXHAUSTIVE_PIPE=1 (`RV_EXHAUSTIVE_PNR_ENV`). aha's
sweep_thesis_collateral.py and tests/test_data_width_e2e.py dropped EXHAUSTIVE_PIPE too.
Stock fabric fw4_dw16_sc8192_sp_in2_out2_vc2_rv, RTL bit-accurate: conv_3_3 4150 ns (static
4149; 1 round, 10 padding registers), tests/down_sample 4150 ns (static 4149; was 7083 with
EXHAUSTIVE_PIPE; 1 round, 4 registers). `aha regress` still sets EXHAUSTIVE_PIPE=1 for its RV
apps (regress_util.py): switching it needs a regression run in the shared /aha (its paths are
hardwired there).

Dense RV runs below one token per cycle whenever a fork's branches rejoin at a PE with
different latencies. Root cause and mechanics are in archipelago CLAUDE.md "Dense RV
throughput"; in short: every hop has a register (`EXHAUSTIVE_PIPE`), registers are
canal `RegFIFO` depth 2 with `ready = ~full`, fanouts are lazy forks, and RV maps with
`MATCH_BRANCH_DELAY=0` / `PIPELINED=0`. So full rate needs the stage counts of the
branches to match exactly at every join (conv_3_3: A 0.750, B 0.667 before).

- **Model** (`common/application/rv_throughput.py`): token-level simulation of the
  routed graph (design.route/place/design_top): REG = 2-deep FIFO with `extra_data`
  initial tokens, PE input/output FIFOs of 2 with the PE's pre-fill (below), an optional
  2-deep primitive output FIFO, lazy forks, MEM outputs / input IO / constant PEs always
  valid, MEM inputs / output IO always ready, a ROM a 3-stage pipeline. Matches xrun on 6 PnR results (0.750 / 0.667 / 0.722 / 0.765 unbalanced,
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
  - Not wired into `aha regress`. `aha pnr --rv-balance N` runs it without PnR pipelining
    (below).
  - A packed pond's output into its own PE is an in-tile wire (route `PondTop_output ->
    PE_input`, no switch box) that holds no register: `Model.fixed`; the plans leave such an
    input early (`early_unpaddable` lists them) instead of padding it (2026-10-28, found by session
    08555638 on resnet_pond with its pack_ponds fix: padding there made netlist creation fail
    with `KeyError: 'rv_balance_...'`). Plans without an early packed-pond input are unchanged.
  - **No padding on a loop through a memory** (user decision 2026-10-28, `Model.loop_in`;
    `Model.unpaddable` = in-tile wire or loop). An accumulation (a MEM or pond output feeding
    back into that memory's input through PEs) is invisible to the model, which treats memory
    outputs as sources and inputs as sinks, and a register on the loop is paid on every
    iteration. Loops are found as strongly connected components of the dataflow graph plus a
    memory input -> output edge per MEM / pond core; a PE input inside one may stay early.
    resnet_pond (thesis RV fw1 dp, 08555638's packing fix): 10 registers / 220,031 ns ->
    8 / 177,697 (= unbalanced 177,694), bit-accurate. pondspec_e2e/resnet (thesis RV fw4 8 KB,
    16x16): 38 -> 32 registers (the three `add_*.data2` loop inputs), 11,677 -> 11,661 ns,
    bit-accurate. Line-buffer apps have no such loop and keep their plans.
  - **PE FIFO pre-fill** (2026-10-28, session cfc4174c). Clockwork realizes a column-offset
    stencil tap by pre-loading tokens into a PE input FIFO: design_top metadata
    `".dataN": {"num_input_fifo": k, "num_output_fifo": j}` on the PE instance (garnet
    core_combiner_core maps `dataN` to `PE_input_width_<dw>_num_N`). The model started every
    PE FIFO empty, so a pre-filled input that must arrive k stages after its partners (its
    pre-filled tokens pair with their first ones) was balanced to arrive with them, stayed k
    early and filled its FIFO. Its fork then stalled. Now `Model.pe_fill` sets `init` on those
    FIFOs, which `arrivals`, the LP (`pad = a(c) - a(p) - 1 + init(c)`, and a PE output's
    arrival minus its pre-fill) and the simulation already honour. camera_pipeline_2x2 (thesis
    RV fw4 8 KB, 28x16; 27 PEs with pre-fill, no other thesis app has any): balanced with the
    old model it ran at 3/4 rate (16,459 ns vs static 12,562; xrun port probes: every input
    accepts 3 of 4 cycles, the fork/join network around the pre-filled PEs blocks itself);
    the fixed model predicts that 0.750 for that design and 0.166 for the unbalanced one
    (measured 73,796 ns). A ROM (design_top `is_rom`) is also modelled as a 3-stage pipeline
    (`Model.rom_tiles`, `("ROM", x, y)`) instead of a source and a sink, so the output IO rate of
    an app whose outputs come from ROMs (camera) is no longer always full; it changes no plan.
  - 1-bit edges (a PE's `O1` / `bit*`, corebit nets) are padded with `corebit.reg` since
    2026-10-18; before that the hook rejected plans that padded them (harris_color).
- Without EXHAUSTIVE_PIPE (2026-10-17, archipelago/CLAUDE.md "RV without EXHAUSTIVE_PIPE"):
  latency matching on the plain routed design (no exhaustive pipelining) beats today's
  exhaustive pipelining: conv_3_3 4153 vs 5533 cycles, gaussian 6393 vs 16969, with about a
  third of the SB FIFOs.
- **`aha pnr --rv-balance N` (2026-10-18, session cfc4174c; aha `aha/util/rv_balance.py`).**
  This is the balancing loop on the `aha pnr` path, for RV without PnR pipelining. An
  explicit N refuses EXHAUSTIVE_PIPE, POST_PNR_ITR and `--daemon`: with no pipelining every
  route hop is a wire, so a padding register adds exactly one stage and placement doesn't
  change stage counts.
  - **On by default since 2026-10-19 (user):** without the flag, `aha pnr` balances
    (3 rounds) whenever DENSE_READY_VALID=1 and none of those is set, i.e. the thesis flow.
    `--rv-balance 0` turns it off. `aha regress` keeps EXHAUSTIVE_PIPE and the daemon for
    its RV apps, so it is unchanged (user decision).
  - Every `aha pnr` first restores a padded `design_top.json` and deletes the last run's
    `bin/rv_balance_{plan,log}.json`.
  After the first PnR, each round does:
  1. Model the routed design (`rv_throughput.model_of`).
  2. Plan with `min_register_plan`, an LP solved with scipy HiGHS:
     - each producer gets one padding chain, shared by its consumers;
     - a PE may start late, to move padding off shared edges;
     - the optimum is integral (the constraint matrix is a network matrix);
     - without scipy it falls back to the greedy `latency_match_plan`.
  3. Insert the registers with `hooks/rv_balance_branches.py --plan --share --pe-stages 0
     --margin 0`.
  4. Pin every block (`manual.place` + `MANUAL_PATH_BALANCE_PLACER=1`).
  5. Run PnR again with `CYCLONE_REG_SEARCH=1` (cgra_pnr thesis c16f471). The stock A* can't
     route long padding chains: harris failed with `req_regs 33`.

  It writes `bin/rv_balance_{plan,log}.json`. A second run first restores the unpadded
  `bin/design_top.pre_rv_balance.json`.

  Results (16x16, fw4_dw16_sc8192 spec, private trees), RV vs static kernel ns, all
  bit-accurate:

  | app | RV | static |
  |---|---|---|
  | conv_3_3 | 4150 | 4149 |
  | gaussian | 6390 | 6389 |
  | pointwise | 4150 | 4149 |
  | fp_pointwise | 4150 | 4149 |
  | unsharp | 17480 | 17470 |
  | harris_color | 17838 | 17816 |
  | resnet | 11677 | 12495 |
  | matmul_rvtry3 | 13355 | 9260 |

  - unsharp needs `RV_FLUSH_FIRST=1` at test time (below).
  - harris converged in 1 round: 530 early stages became 256 padding registers. The greedy
    plan, or the stock router, did not route.
  - matmul is limited by its pond recurrence, which balancing can't fix ("Why RV runs
    slower" below).
- **Testbench `RV_FLUSH_FIRST=1`** (`tests/test_app` make variable, passed as `+RV_FLUSH_FIRST`):
  `Env_rv_flush_then_unstall` flushes the array before releasing stall. This fixes the RV
  kernel-start race that unsharp hits. `aha test` sets it when the app's last PnR was
  balanced (`bin/rv_balance_log.json`) and RV_FLUSH_FIRST is unset. The testbench default
  is unchanged.
- **Pitfall: an app dir copied from another run runs that run's bitstream.**
  `hw_support/parse_design_meta.py` used to name the first `*.bs` in bin/ (os.listdir order)
  in design_meta.json. A copied run directory therefore simulated its old unbalanced
  bitstream, and balanced harris looked stuck at 1/3 rate. Since Halide-to-Hardware thesis
  (2026-10-18) it takes the newest `*.bs`.
- Tests: `tests/test_app_bundle_guards/test_cgra_app_power.py` (hook naming and
  idempotence, fork imbalance, parity output FIFO, placement, 1-bit padding, the
  unpipelined latency-match plan, the LP plan with a shared chain). The `aha pnr` side:
  aha `tests/test_rv_balance.py`.

## PE-tile pond knobs (Tile_PE with / without / spec pond) (2026-09-30)

`Tile_PE` uses the same shared `common/rtl` step as Tile_MemCore (whole-chip
`garnet.py` → synth picks the `Tile_PE` top), so it builds on the build machine
as-is; none of the MemCore-specific nodes (spec SRAM macro, die-grow
floorplan, `mode[0]` guard) apply — the pond is flops, no macro.

- `NO_POND=True mflowgen run --design .../Tile_PE` → rtl param `no_pond` →
  `garnet.py --no-pond`. **`--no-pond` never worked in onyx before
  2026-09-30**: `get_cc_args` had `args.add_pond = not args.no_pond,` (trailing
  comma → 1-tuple → always truthy); fixed. The same bug on
  `args.add_pd = not args.no_pd,` made `--no-pd` (passed whenever PWR_AWARE is
  False, incl. every MemCore sweep build) a no-op until 2026-10-18 (fixed with
  the user's OK, with `pond_area_opt(_dual_config)`, which onyx ignores);
  `tests/test_cc_args` checks that every bool reaches `create_cgra` as a bool.
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
- **Clock gating is lake's default since 2026-10-28 (user), and sweep configs are
  explicit.**
  - `sweep_specs.py` writes `share_clk_ctr` / `clock_gate_ports` into every
    spec_config.json and `pond_spec.json` (`_power_options`: on only for
    `_sharectr` / `_portcg` names). A stock config's spec_config.json goes unused and
    stays `{}`; its spec pond's `pond_spec.json` is explicit (ungated).
  - The standalone synth command passes `--[no_]clock_gate_ports` /
    `--[no_]share_clk_ctr`. Before this it passed neither, so a `_portcg` config's
    standalone lakespec was ungated. It needs the host lake pulled.
  - `with_mem_power_options` passes a MEM spec's explicit False to the pond too.
  - `check_bundle.py` (SPEC_DEFAULTS) and `cgra_app_power.py` (`recorded_spec`)
    read a bundle spec without the keys as ungated: every bundle recorded before
    the flip.
  - `gen_app_bundle.py` records the options explicitly in the bundle's spec (and builds
    from that file): `--spec <json>` and a stock `--config` get lake's defaults
    (`explicit_power_options`).
  - What changed hardware: anything that builds lake specs without these keys.
    That is garnet's built-in MEM spec (Zircon, no LAKE_SPEC_CONFIG), the default
    RV pond, and spec JSONs that leave the keys out. Stock legacy cores
    (StrgUBVec, PondCore) aren't lake specs and don't change.
- **Clock gating reaches the pond (2026-10-22, session 5b33d095; user: "the pond
  (and any lake-based spec) should see the clock gating").**
  - The pond takes lake's `clock_gate_ports` / `share_clk_ctr` as pond-spec keys
    (lake ca947229).
  - When its JSON doesn't set them, a lake-spec pond (RV mode, or a static spec
    pond) inherits them from the MEM spec config (`LAKE_SPEC_CONFIG`). The helper is
    `with_mem_power_options` in `cgra/util_onyx.py`, used by `make_pond()` and
    `cgra/util_thesis.py`. So a `_portcg` / `_sharectr` spec gates the MEM and the
    pond, and the thesis opt specs gate the thesis PE tile's pond too.
  - `{"clock_gate_ports": false}` in the pond JSON keeps the pond ungated. The
    legacy `PondCore` is unchanged.
  - An RV pond also inherits lake's `rv_comparator_trim` (`SPEC_RV_OPTIONS`, 2026-10-25); the
    static pond doesn't take it.
  - No gating in the MEM spec leaves the pond params untouched (None included), so
    other builds keep their RTL.
  - Tests: `tests/test_spec_power_options`. Bit-accurate matmul_rvtry3 on gated
    static and RV thesis CGRAs (lake CLAUDE.md §5.6).
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
  Correction (2026-10-17): no case analysis is set on the mode/bypass config bits, so STA
  times the PE input-FIFO bypass branch (`bypass_rv` / `fine_grain_fifo_bypass`), which only a
  static or pond-feedback PE uses; in a dense-RV PE the path starts at the input FIFO. With the
  bypass bits pinned, local R2R is 3270 ps RV / 3611 ps static (was 4593 / 4102). The thesis
  fabrics remove the dead hardware instead: see "Thesis fabrics".
- **PE tile through PnR at 400 MHz (2026-10-18, session 1fa8a391; zip
  `/aha/pe_tile_specpond_r8cad-gf12_20261018-182758.zip`):** `--spec-set pe_tile --only
  stock_specpond` (garnet's stock PE tile on the default READY-VALID interconnect, with lake's
  default spec pond in static mode; spec set `pe_tile` was removed 2026-10-24, so rebuild it
  with `--replace --extra-specs` of `[{"stock": true, "pond": "spec", "runtime_mode": "static"}]`;
  a static-fabric PE is the thesis static fabric, `--spec-set thesis_fabric`), garnet before 6f110058
  (so with power-domain logic). Synth: cells 9357 um2, WNS -15.6 ps (Genus spent 4.2 h on it on a
  loaded machine). PnR: 10301 um2 (PE 3371, PondCore 2788, SB B17 2326, SB B1 684, CBs ~600,
  PowerDomainOR 39). Innovus signoff: R2R +0.177 ns, R2O +0.172, I2R -0.314, I2O -0.319; hold
  met. PT's -0.885 ns is NOT valid: Tile_PE's signoff had no fix-pt-sdc.tcl, so PT's read_sdc
  stopped at line 4291 (append_to_collection) and dropped the rest, the `tile_id` false path
  among them (every top PT path started at tile_id). Now (same commit as this note)
  Tile_PE runs fix-pt-sdc.tcl (Tile_MemCore/custom-signoff) after generate-results.tcl and
  fails PT/genlibdb on "Errors reading SDC" (test `test_tile_pe_pt_reads_the_whole_sdc`).
  PE workspaces signed off before it: use Innovus's WNS, or re-run PT by hand on a folded SDC.
  The failing synth paths (top 50, all -14..-16 ps) are two kinds, neither the PE's own R2R:
  (1) 34: a fanned-out track's ready -> valid (canal `ReadyValidLoopBack` valid = core valid &
  consumers' ready, and the SB fan_in AND), constrained as one SB hop (`sb_delay` 210 ps +
  i_delay, constraints common.tcl) but AND + fan-in + AND + 2 muxes, ~226 ps, and after PnR it
  crosses the tile; (2) 16: a 1-bit track selected as flush (`CB_flush`) -> static pond flush
  -> pond valid -> PE input valid -> PE (input-FIFO bypass branch) -> res_p -> SB -> B1 FIFO
  register, timed as a single-cycle input path though flush is a once-per-run pulse.
  Innovus path reports were not in that zip (zips carry them since REPORT_ZIP_GLOBS).
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
- With both fixes, RV ux=4 still hung on the stock fabric: a standalone RV pond fed over the
  interconnect forms a valid/ready loop with the SB/CB lazy fork (lake/CLAUDE.md §6 "RV pond
  ready depends on valid"). `--thesis rv` fixes it with canal's pond-input CB FIFO (d83e892).
- 2026-10-28 (garnet/thesis-unpacked-pond-output): the one-pond-per-PE rule let an input-side
  claim take the PE of a pond that `find_packing` had kept on output 0 (resnet_pond: the
  accumulator went into its writer's tile, so weight bank M4 stayed unpacked on output 0). On
  the thesis fabric output 0 is inter-core only, so Cyclone could not route it. Now a pond
  on output 0 takes the PE that output feeds before any other claim (`find_packing` keeps
  at most one such pond per PE). resnet_pond thesis RV fw1_dw16_sc4096_dp_in1_out1:
  routes, bit-accurate (177,694 ns with `--rv-balance 0`); matmul_tile thesis rv/static
  T84, T44u4, T84u4: packing and bitstreams identical.

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
  `a16b3973-.../scratchpad/p32/patches/*.patch` are the 2026-10-08 env-knob version, superseded on
  2026-10-10 (see "One source of truth" below). The private trees `p32/aha`, `p33/aha` and `s32/aha`
  were deleted on 2026-10-19 to free disk; their drivers, logs and patches are kept.
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
  - **All 24 through PnR (user request 2026-10-17):** per-width PnR numbers instead of
    projections. The `memtile` recipe now builds preset `dw8_32_64` through PnR, held out
    of the dw16 fit (test `test_memtile_recipe_pnr_at_every_width_dw16_fit_only`). The run
    is step 4 of "Build machine: thesis data runs" below. Per width: dw8 12 (9 static,
    3 RV), dw32 8 (6, 2), dw64 4 (3, 1); fw4 at dw64 has no macro.
  - **Result (2026-10-21, all 36 `memtile_pnr` tiles, zip
    `memtile_r8cad-gf12_20261021-031739_slim`, garnet 13732565, RTL lake de6b95c5, no power
    domains; analysis in `/aha/sweep_out/memtile_pnr_20261021/README.md`):**
    - **36/36 PASS** through PnR, PT and synth/PnR idle/active power. These real PnR numbers
      replace the projections for all 24 dw 8/32/64 configs.
    - The dw16 fit (8 tiles) on the 28 held-out tiles:
      - total area within 1% at dw8/16/32; dw64 is 1-3% above the projection;
      - active power within 8% (dw64 5-8% above);
      - idle power off by up to +18% (fw8 dw8 vc8) and -18% (the one dw64 RV tile).
    - **Per-width fits** (each width's own static tiles, leave-one-out) beat it. Worst error
      at dw8: area 0.25%, idle 4.7%, active 1.6%. At dw64: area 0.8%, active 1.9%. RV has too
      few tiles per width (3/2/1) for its own fit. `perwidth_fit.csv` and the script are in
      that directory.
    - **The idle miss is a synthesis-level artifact, not a width effect.** The SRAM macros
      match between synth and PnR. Internal power in the lake core drops at PnR in some
      tiles: -11 to -13% in fw8 dw8 vc8 and fw8 dw8 vc2 RV. Across the 28 held-out tiles that
      drop tracks the idle error (Spearman -0.84). This is consistent with synthesis booking
      the logic-gated core clock as one unbuffered net ("MemTile idle/active power").
  - **First run (2026-10-17/18, standalone command, garnet 96ff8af8; zip
    `tile_memcore_dw8_32_64_pnr_r8cad-gf12_20261018-071557_slim`, analysis in
    `/aha/sweep_out/dw8_32_64_PNR_20261018/README.md`):** 10 of 24 through PnR, 4 with power.
    - **Every failure was environmental.** From ~05:43 the build machine's docker data root
      (`/sim/docker`) was full. Every rtl and memtile-power-test-gen step after that failed at
      `docker run` ("no space left on device"): 12 RTL, 6 power. Two RV PnRs were `Killed` in
      postroute (~8 GB each, 6 jobs at once, likely OOM).
    - **PnR is deterministic.** The three tiles built both here and on 2026-10-14 match exactly in
      area, PT WNS and power, and their signoff area reports are byte-identical.
    - On the 13 tiles at other widths that now have PnR, the dw16 fit holds total area within 2.3%.
      Static dw8 is within 0.6% across fw2/4/8 and vc2/4/8.
    - **Rerun:** superseded on 2026-10-18 by the user's call to rebuild from scratch on current
      branches: preset `memtile_pnr`, step 4 of "Build machine: thesis data runs". The note below
      is why a resume would have had to stay on 96ff8af8.
      The original plan: the same command with `--skip-existing --config-jobs 4`, into the same
      out-dir, after freeing `/sim/docker`. Keep the build machine's garnet at 96ff8af8 until it finishes.
      The rtl and memtile-power-test-gen steps copy the host garnet in when they run, and from
      6f110058 on, `--no-pd` (every MemCore sweep) drops the power-domain logic. That logic is
      about 0.2% of a dw32 tile's area in the PD config register + PD OR alone, plus some
      SB/CB gates. The finished tiles and the dw16 fit all have it.
- **Thesis fabrics at dw 8/32/64 (2026-10-22, session a16b3973; user: extend the thesis fabrics
  to other data widths).** `cgra/util_thesis.py` and `ThesisGarnet` follow the spec's width.
  Findings, all on /aha:
  - **RTL:** a 4x2 thesis build at dw32, static and RV, has B1 + B32 switch boxes,
    MEM/PE/pond/IO data ports at 32 bits, PE `inst` [131:0] and GLB `CGRA_DATA_WIDTH` 32. No
    17- or 33-bit tracks.
  - **memtile-power-test-gen on thesis tiles:** dw 8/32/64, static and RV, idle and active all
    PASS. xrun runs it as `run_sim.sh` does: `+define+MEMTILE_SAIF_TCL -input cmd.tcl`, which
    current testbenches need. Data runs on whole-word B8/B32/B64 tracks.
  - **Apps:** 12 thesis cases in aha `tests/test_data_width_e2e.py`, all bit-accurate.
    - Static: arith dw32/dw64, conv_3_3 dw32, the scalar_reduction pond dw32,
      conv_3_3_u8 dw8.
    - RV: arith dw32/dw64, conv_3_3 dw32, conv_3_3_u8 dw8, and matmul_bounded (pond
      accumulation) at dw 8/32/64.
    - Halide-to-Hardware thesis added `tests/conv_3_3_u8` (uint8 sums) and
      `tests/matmul_bounded` (2-bit inputs). Their values are exact at those widths; a u16
      app's are not.
    - **Gated by default since lake 14d9f070:** the test's spec JSONs leave out
      `share_clk_ctr` / `clock_gate_ports`, so all 20 cases (8 stock + 12 thesis) now build
      gated MEM and pond RTL (`gclk` in garnet.v). Re-run 2026-10-29 at garnet ebda5a58:
      20/20 bit-accurate (2 h 36 min).
  - **Fixed on the way:**
    - The rv_balance hook made padding registers as wide as a PE instruction constant: 132 bits
      at dw32, so PnR died. Now it uses the fabric width: garnet ac4d9348, aha 923441d.
    - lake `build_spec_rv` refused RV fw2 dw64 dual-port ("No valid macros", a one-column check):
      lake b59ea334.
  - **Not width issues:**
    - `tests/down_sample` failed clockwork's compile_mem on a lake-spec MEM at every width (isl
      assertion) until Halide thesis 9e9966a53 (session 43d74890) unrolled its 2x2 reduction. It
      now compiles static and RV, so it can serve as a dw8 app.
    - `apps/scalar_reduction` has only a static `hack_design_top.py` rewrite, so it can't run RV.
    - No FP at dw != 16 (`gen_PE_fc(dw)` is the integer PE).
  - **dw32 RV RTL before gemstone thesis c3f0acc (2026-10-23, cfc4174c) defined two different
    `mux_logic_32_{2,5}` / `precoder_32_{2,5}` modules** (RV data muxes and plain 32-bit config
    muxes). Genus kept the wrong one and failed elaboration; xrun keeps the first, so the sims
    passed. Re-run on c3f0acc: dw32 RV arith, conv_3_3 and matmul_bounded still bit-accurate, and
    the 16x16 garnet.v has no duplicate module names. Only dw32 RV has the clash: dw8/dw64 tracks
    and the stock fabric's dw+1 tracks differ from the 32-bit config width.
  - **Tile_PE constraints don't depend on width:** `mul_path`/`add_path` name widths but are
    unused, and the FP false paths are `_if_pins_exist`. gf12 sweeps at dw 8/32/64 on thesis
    tiles: cfc4174c's `--spec-set thesis_dse` / `thesis_pe_widths`, `--recipe thesis_fmax`.

## Thesis fabrics: garnet.py --thesis static|rv (2026-10-17, session cfc4174c)

Why: a "static" lake-spec build (`--lake-spec-mode static`) was the RV+sparse fabric with
the FIFOs bypassed by config: 2-deep FIFOs on every SB track/side (run as plain registers),
ready/valid, 17-bit tracks (the 17th bit is sparse's end-of-stream token), the RV IO tile,
PE input/output FIFOs + bypass muxes, all 8 PE primitives (6 sparse-only), and the static
MEM ports' FIFOs + `*_bypass_rv` muxes. Every static-vs-RV area/power number before this
charges static for RV + sparse hardware. `--dense-only` (the only non-RV fabric) crashed at
HEAD and ignores the lake spec.

What (user decisions 2026-10-17): `garnet.py --thesis {static,rv}` -> `garnet_thesis.py`
`ThesisGarnet` (a Garnet subclass: builds its own fabric with `cgra/util_thesis.py`
`create_cgra_thesis`, inherits the GLB + PnR/bitstream code unchanged). Needs
`--lake-spec-config`; sets LAKE_SPEC_MODE to the mode; rv sets USE_NON_SPLIT_FIFOS.
- static: canal `ready_valid=False` (SB track = flop + bypass mux), tracks [1, dw];
  PE `CoreCombinerCore([OnyxDensePE(dw)])`; MEM `build_spec(config_passthru, comply_17=False)`
  + StrgRAM + StencilValid; static spec pond; all with lake `hybrid_policy="static"` (no
  port FIFOs, no tile valid/ready, no bypass regs); IO `IOCore(dw)` (one register each way:
  same latency as the RV IO FIFO, so static schedules are unchanged).
- rv: canal `ready_valid=True` (SB FIFO + bypass mux kept), tracks [1, dw] (no EOS bit,
  ready/valid separate wires); PE = lake `OnyxDenseRVPE` (OnyxPE without static mode,
  EOS/maybe logic and sparse; keeps the configurable prim outfifo) with
  `hybrid_policy="rv"`: all 8 PE ports (data0-2, bit0-2, res, res_p) have their tile FIFO
  (+ bogus_init pre-fill config), no `*_bypass_rv` / `*_fine_grain_fifo_bypass`; MEM
  `build_spec_rv(comply_17=False)` + StrgRAMRV; RV spec pond (fifo_depth 0, as before);
  IO `IOCoreReadyValid(tracks [1, dw])`.
- Neither has sparse cores. Layout, SB topology, global signals, GLB: as util_onyx.
- PnR/bitstream: same flags + `--thesis` for `aha pnr`; static apps = DENSE_READY_VALID unset
  everywhere, rv apps = DRV=1 (ThesisGarnet.place_and_route refuses a mismatch).
  `ThesisGarnet.load_netlist` sets mapper `set_rv_track_eos_bit(False)` (dw-bit buses).
- `--no-pd` is ignored: `ThesisGarnet` never passes `add_pd`, so thesis fabrics always
  have power domains (util_onyx `--no-pd` builds have none since 2026-10-18).

Library pieces (all default off; existing RTL unchanged: lake-spec RV build byte-identical,
static-spec / default / Zircon identical up to kratos statement-order and `_unq0` naming
nondeterminism, which two pristine builds also show):
- lake: MemoryTileBuilder/CoreCombiner `hybrid_policy` ("bypass" default, "rv", "static";
  "static" raises on a true RV port); controller attr `rv_1bit_ports` (1-bit ports on the
  RV interconnect, like reduce_pe_cluster); `build_spec` / `build_spec_rv` / `build_pond_rv`
  `comply_17` (default True); `lake/modules/onyx_dense_rv_pe.py`; tests/test_hybrid_policy.py.
- canal: `__wire_flush_to_sbs` skips switch boxes without a flush port (non-RV).
- garnet: CoreCombinerCore `hybrid_policy`, `has_config` guards on the RV PE config regs,
  bogus-init names from the PE port remap width; `IOCore(data_width)`; wiring_onyx uses
  `garnet.data_track_width`; mapper `set_rv_track_eos_bit`; garnet.py io-port remap when the
  track width is not 16/17-as-default; tests/test_thesis.
- mflowgen: rtl param `thesis` (gen_rtl.sh passes `--thesis`; in the container it fetches
  canal branch thesis, whose flush fix the image lacks), Tile_PE/Tile_MemCore construct.py
  read THESIS_FABRIC; sweep_specs knob `thesis` (name suffix `_thesis`), spec set
  `thesis_fabric`, preset `thesis_fabric_pnr`, recipes `thesis_mem`, `thesis_pe`
  (`thesis_fabric` = both). Constraints: env PT_I_DELAY_FRAC makes the flush/stall/config
  input delay a fraction of the clock (thesis recipes: 0.25; unset = the fixed 0.7 ns);
  generate_testbench follows it.

Verified (private trees; scratchpad cfc4174c thesis/run_app.sh, chain.sh; fw4_dw16_sc8192_sp_in2_out2,
16x16, RV with EXHAUSTIVE_PIPE=1): every app bit-accurate on both fabrics, kernel ns static / RV:
conv_3_3 4149 / 5533, gaussian 6389 / 12755, pointwise 4149 / 4150, fp_pointwise 4149 / 4150
(`aha test --dense-fp`, as the regressions run fp apps: 78/4096 outputs are 1 bf16 ulp off the
Halide gold in both modes), unsharp 17470 / 156763, harris_color 17816 / 165807, matmul_rvtry3
(static/RV spec pond) 9260 / 13364, resnet 12495 / 12783 (app copy with the output channel
innermost, `pondspec_e2e/resnet` + EXT=mat: stock apps/resnet stops in parse_design_meta
"inner dim 28 ... unroll 3"). Every static number equals the old static-on-RV-fabric run (the IO
register keeps the schedules' latency); RV equals the old RV runs except gaussian (16969 on the
2026-10-06 toolchain).
Structure: tests/test_thesis (4x2: static tiles have no FIFO modules and no _ready/_valid,
only the GLB DMA FIFOs remain; RV PE has 8 ports each with valid/ready + tile FIFO; neither
fabric has sparse modules or bypass config; tracks {1, 16}; RV switch-box registers are
`FifoRegWrapper_*_fifo_only` with no `fifo_en`).
RV switch-box registers are always FIFOs (2026-10-19, user decision): canal's `fifo_en=0`
mode is a plain register (`valid_out` and `ready_out` stuck at 1, simulated) that loses
tokens on an RV route. `util_thesis.py` passes canal `fifo_only_regs=True` for `--thesis rv`,
which removes the mode bit and its muxes; the register mux remains the bypass. Stock
fabrics keep the mode (static apps use it). Details: canal/CLAUDE.md "Switch-box registers
that are always FIFOs".
RV pond input: since 2026-10-21 (user chose this over a lake fix) the pond's input CB has a
2-deep FIFO on its switch-box sources, and the inter-core loopback (a packed pond fed by its
PE) bypasses it (canal `input_fifo_ports`, util_thesis passes `PondTop_input_width_{dw}_num_0`
for `--thesis rv`).
- Without it, an unpacked RV pond fed over the network looped: its ready is its grant, which
  needs valid, and the CB valid is gated by that ready. matmul_tile `ux=4` hung.
- Packed ponds are unchanged (matmul_rvtry3: same bitstream, 13355 ns). Network-fed pond
  writes take +1 cycle. Local freepdk45 Tile_PE +0.6% area.
- MemTile RTL is unchanged. Details: canal/CLAUDE.md "Network-side FIFO in a core input's CB".

Running apps (recipe: `aha --dir <private aha tree>` with garnet = a private copy and
GARNET_HOME pointing at it): `garnet.py --thesis MODE --lake-spec-config spec.json
[--lake-pond-spec-config pond.json] --width W --height H --verilog --use_sim_sram`, then
`aha map --collateral <spec collateral> --pond-collateral <pond collateral of MODE>`,
`aha pnr ... <same garnet flags>`, `aha test` (static: no DENSE_READY_VALID; rv: DRV=1
PIPELINED=0 MATCH_BRANCH_DELAY=0 at halide/map, DRV=1 at pnr/test).
Export LAKE_COLLATERAL_JSON_MEM (and _REGFILE with a pond spec) for `aha pnr` too, not only via
`aha map --collateral/--pond-collateral`: static `aha pnr` (--pipeline_pnr) re-runs clockwork
(`make reschedule_mem`) with the current env, and without them it reschedules against clockwork's
default collaterals (08555638: thesis static matmul_tile 8x4, 7/256 outputs wrong; bit-accurate
with both exported). gen_app_bundle.py already exports both for pnr.
Pitfall (cost hours): reusing one garnet.v across apps also needs every file garnet.py
writes for that array: global_buffer/header, global_controller/header, matrix_unit/header,
*/systemRDL/output (+ glb.rdl, glc.rdl.final) AND genesis_verif/ (the global controller's
Genesis RTL). A 16x16 garnet.v with a 4x2 genesis_verif/RDL leaves the GLB flush-crossbar
select floating: no flush reaches the tiles, the static stencil_valid never starts, STRM_F2G
times out ("got interrupt, but not from STRM_F2G"). RV apps may survive it.

gf12 (build machine, garnet + lake pulled; outputs under /nsim/mstrange/BUILDS):
`./mflowgen/sweep_specs.py --recipe thesis_mem --out-dir /nsim/mstrange/BUILDS/sweep_out/thesis_fabric --zip --zip-slim`
(MemTile static + RV through PnR, PT_I_DELAY_FRAC 0.25: 2 builds); `--recipe thesis_pe` = the
PE tile pair, `--recipe thesis_fabric` = both (4 builds).
**One clock for every thesis tile (user 2026-10-21): the slowest block's.** The CGRA runs at
one clock, so a tile synthesized faster than the array can run is upsized for nothing.
(Refined 2026-10-22: each (static|RV, data width) CGRA at its own slowest tile's clock; see
"Thesis design-space sweep" below. The 400 MHz parts here are the 2026-10-22 tile set.)
- `THESIS_CLOCK_MHZ` (= APP_POWER_MHZ, 400) is the clock in every thesis part (thesis_mem,
  thesis_pe, thesis_mem_opt). The MemTile used to default to 750 and the PE to 400.
- The slowest block is the PE: the stock PE is ~2.45 ns at gf12; the thesis PEs are ~1.8 / ~1.5
  ns static / RV by a local estimate.
- `--recipe thesis_fmax` measures the real limit: the optimized MemTiles and the PE pair,
  synthesis only, at 1000 MHz, no power. A tile's limit is ~1000 / (1 - WNS_ns) MHz.
- Then build at the slowest tile's limit (minus PnR margin) with `--recipe thesis_opt
  --clock-mhz <F>`. A top-level --clock-mhz re-clocks every part together.
- Use the same F for cgra_app_power.

**gf12 results (2026-10-22; zips thesis_fmax_{mem,pe}_r8cad-gf12_20261022-*, thesis_{mem_opt,pe}_
r8cad-gf12_20261022-*; extracted in /aha/sweep_out/thesis_fmax_20261022 and thesis_opt_400mhz_20261022).**
All 10 builds PASS.

Clock probe (synthesis at 1000 MHz):

| tile | WNS | limiting path | limit |
|---|---|---|---|
| 3 optimized MemTiles | 0 / +0.1 ps | — | >= 1000 MHz |
| RV PE | -594 ps | reg->reg: config reg -> ALU -> 1-bit output FIFO | ~1.59 ns, ~627 MHz |
| static PE | -891 ps | in->reg: track -> CB -> combinational ALU -> 1-bit res_p -> SB register | 1.59 ns after the 0.3T input delay: 1.59 / 0.7 ~ 440 MHz |

- The static PE has no registers, so its path crosses tiles. With a ~150 ps upstream share
  instead of 0.3T it would reach ~570 MHz.
- **400 MHz is the slowest block's clock with PnR margin, so the thesis_opt build at 400 is
  the tile set.**

Tiles at 400 MHz (PnR area um2, PT setup WNS, PnR-level idle / active power mW):

| tile | PnR area | PT WNS | idle | active |
|---|---|---|---|---|
| static MemTile, shared ctr + port gating | 12,691 | -11 ps | 0.455 | 5.50 |
| RV MemTile, gating + FIFO-8 filter | 14,661 (+15.5%) | -10 ps | 0.667 | 5.70 |
| RV MemTile, gating + no filter path | 13,578 (+7.0%) | -9 ps | 0.597 | 5.63 |
| static PE | 6,040 | -38 ps | | |
| RV PE (pond input FIFO) | 7,827 (+29.6%) | -64 ps | | |

- The worst paths are tile feedthrough budgets: static PE track in -> 1-bit SB out; RV PE and RV
  MemTile switch-box ready -> valid.
- 16x16 array area (192 PE + 64 MEM tiles, no IO/GLB): static 1.97M um2; RV FIFO-8 2.44M
  (+23.8%); RV no filter path 2.37M (+20.3%).
- The 2026-10-18 non-optimized pair at 750 MHz was 13,114 / 15,766 (+20.2% for the MemTile). The Tile_PE constraints were sourced on the thesis PE RTL (local Genus 20.11,
2026-10-17) with no errors; the pond path resolves to the spec pond's. The spec point is lake's default
spec (build_spec defaults: fw4 dw16 4 KB 2x2 single-port vc2; user 2026-10-18; it was 8 KB,
the app matrix above, until then). Add `--clock-mhz` / `--stop-after cadence-genus-synthesis`
for an over-constrained fmax probe.

**Thesis design-space sweep: each fabric and width at its own clock (user 2026-10-22, session
cfc4174c).** User decisions:
- RV MemTile = clock gating + no filter path (`_nofp_portcg_thesis_rv`); static = shared counter +
  port gating (`_sharectr_portcg_thesis`). `THESIS_OPT_KNOBS`, `_thesis_opt()`.
- Clock per (static|RV, data width) CGRA = 0.9 x its slowest tile's synthesis limit, rounded down
  to 5 MHz. The PE is the slowest at dw16 (MemTiles >= 1 GHz).
- Static PE limit with a realistic upstream budget: its slowest path starts in the neighbour's
  register (track -> CB -> combinational ALU -> 1-bit res_p -> SB register, 1.59 ns of logic), so
  every thesis tile's data/valid/ready inputs get a fixed `TILE_I_DELAY_NS` = 0.23 ns
  (`--i-delay-ns`, `THESIS_I_DELAY_NS`; both tile SDCs and the replay testbench read it) instead
  of 0.3T (PE) / 0.2T (MemTile). Expected ~549 MHz static (clock ~490) vs ~627 RV (clock ~560) at
  dw16; it was ~440 under 0.3T.
- Why fixed and why 0.23 (user asked 2026-10-22 whether a fixed budget is fair): the upstream
  share is the neighbour's SB register clk-to-q, its register mux and the abutted wire, none of
  which scale with the clock. A fraction of T charges the static PE (input-started critical path)
  T >= L / (1 - a) instead of L + d (+0.68 ns at 0.3T) while the RV PE (internal reg->reg limit)
  barely notices, so it is not neutral. Block-level percentages (20-50%) are heuristics for an
  unknown driver; the CGRA literature (Cascade, Melchert et al. TCAD 2024, archipelago's STA)
  composes absolute per-path delays measured on post-PnR GF12 tiles. 0.23 = archipelago's `rmux`
  (SB register -> register mux -> SB out); first set at an estimated 0.15, switched the same day
  (static limit ~574 -> ~549 MHz). It assumes archipelago puts a register just before each static
  PE input; each unregistered SB hop adds ~140-210 ps, so app-level STA gives the real static
  clock. A thesis_fmax run at 0.15 must be re-run (the probe's input delay is in its limits).
- RV has no vec_capacity > 2 at fw > 1: lake's RV wide-fetch port has a fixed 2-entry
  write-combining/read buffer (`max_num_items_wcb = 2`, lake/spec/port.py), which already gives
  full rate under handshakes; build_spec_rv refuses vc > 2 rather than size unused storage. The 18
  RV twins stay out (vc is a static-only axis).
- Data widths 8/32/64 are in (session a16b3973 owns the functional side: thesis apps, power-test
  gen and Tile_PE RTL at those widths; dw16's PE has the bf16 FPU, which sets its limiting path,
  other widths are integer-only).

Recipes (all write under one --out-dir; `--clocks-from <that dir>` reads the probe):
1. `thesis_fmax`: `thesis_fmax_mem` (spec set `thesis_mem_widths`: the chosen MemTile pair at
   `THESIS_WIDTH_POINTS`, dw16 = fw4 4 KB design point, dw8/32 fw4 sc8192, dw64 fw4 sc16384;
   dw64 was fw2 sc8192 until 2026-10-28, SRAM-limited at 2x2) +
   `thesis_fmax_pe` (`thesis_pe_widths`: the same specs, options included, so the PE tile's
   pond is gated as in the CGRA, garnet c9c6da9b), synthesis at 1000 MHz: 16 builds, plus
   `thesis_fmax_pe_regops` (4 static PEs timed with registered operands, garnet 6f0b1485) = 20.
   `--clocks-from <out>` takes the regops limits for static Tile_PE when that subdir exists.
2. `thesis_tiles` (needs --clocks-from): `thesis_tiles_mem` (the dw16 MemTile pair, preset
   `thesis_design_point`, PnR + idle/active power) + `thesis_tiles_pe` (PE pair at 4 widths, PnR).
3. `thesis_dse_reduced` (92 configs, 16 PnR) and `thesis_dse` (246 configs, 38 PnR): spec set
   `thesis_dse` = DEFAULT + thesis specs + `_thesis_width_points()` (25 more dw 8/32/64 specs, all
   with RV twins), both modes, synthesis + synth-level power for all.
   - **Balanced width points (user 2026-10-28).** Equal-bandwidth comparisons must not show an
     SRAM wider than its ports can use, or ports the SRAM can't feed. Balanced = fetch width =
     in + out ports (single-port) or = ports per direction (dual-port). Per width: the smallest
     tile (fw1 sp 1x1 4 KB: a one-word single-port SRAM can't be balanced, so it is only the
     model's anchor), then the dw16 MEMORY_EXP's six organizations: sp fw2 1x1 8 KB, sp fw4 2x2
     (dw8 4/16/32 KB, dw32/64 16/32 KB: no fw4 macro below 8 / 16 KB), sp fw8 4x4 (16 KB, dw64
     32 KB) and dp fw1 1x1 / fw2 2x2 / fw4 4x4 at 8 KB. They replaced (2026-10-28) the 10-25 set's
     unbalanced points: fw1 2x2, dw32/64 capacity and port points at fw2 2x2 / 4x4, dw8 fw4 1x1 /
     4x4, dw64 dp fw1 2x2. Every new spec builds in lake build_spec / build_spec_rv (static + RV);
     tile RTL not regenerated locally. dw64 dp fw2 builds since lake b59ea334 (the spec check
     splits the 128-bit word over two SDPB columns, as CoreCombiner does).
   - The thesis set's own unbalanced points stay: the port grid (fw2/4/8 x vc at 2x2) and the
     IterationDomain / affine sweeps (fw1 2x2) vary one parameter at fixed ports, for the model and
     the component figures. lake's equal-bandwidth figures plot only balanced organizations
     (`tile_figures._balanced`).
   - The 10-25 run (zip thesis_dse_mem_..._20261025-173346) has the old width points.
   PnR anchors per (mode, width): `_DSE_FIT` (dw16 = the dw16_fit8 geometries, others 3 each) and
   `_DSE_VAL` held out (dw16 = design point + dw16_val4 geometries, others 1 static + 1 RV).
   Reduced = dw16 fit + design point + the other widths' held-out tiles (projected from dw16).
- **Final thesis data set (plan 2026-10-25/26, session bc48e85f; every form dry-run on garnet
  4bef22b0+).** User 2026-10-26: keep the RV tile output FIFOs (they add little; estimate their
  removal later from the tile-set per-block area/power), no RV comparator trim, app bundles for all 8
  lake DESIGNS_SINGLE_LEVEL points (dw8/dw32 included; camera_pipeline_2x2 on a bigger array if 16x16
  does not place, since power replays single tiles), whole-CGRA power with `--pe-registered-operands`
  (the user expects the Cond rewrite may make the bypass-path static clock close enough; the
  thesis_fmax probe measures both). Later the same day: keep the registers on the 1-bit tracks;
  the standalone RV filter path is not kept, so the data set carries a small A/B showing what it
  would cost / save: `--recipe thesis_filter_ab` (five RV MemTile geometries, each without the
  filter path and with the FIFO-8 one, all through PnR + idle/active power; the no-filter-path half
  is the thesis_dse tile), plus conv_3_3 bundles on the two fw4 dw16 2x2 geometries (4 KB design
  point, 8 KB): A0 on `_nofp_portcg_thesis_rv`, A and B on `_ff8_portcg_thesis_rv` (B = `--env
  METAMAPPER_MEM_PORTS=3 --pre-pnr-hook <tree>/garnet/mflowgen/common/application/hooks/
  conv_3_3_eat_rows_up_front.py`; the hook only handles conv_3_3's single line-buffer MEM).
  - **Re-probe with the Cond rewrite (2026-10-27; `--recipe thesis_fmax --out-dir
    /nsim/mstrange/BUILDS/thesis_final`, lassen 0f44a74 in every rtl log; zips
    thesis_fmax_pe{,_regops}_r8cad-gf12_20261027-{025826,062238}_slim, extracted in
    /aha/sweep_out/thesis_fmax_20261027/zip).** 12/12 PASS. Synth limits, MHz at dw 8/16/32/64:
    static PE with registered operands 798/668/633/568, without them (bypass path) 785/660/624/552,
    RV PE 968/779/728/628 (was static regops 648/554/534/481, RV 749/639/602/535). The MemTiles
    stay >= 1 GHz (10-23 probe; the 10-26 thesis_fmax_mem zip isn't on /aha), so the PE still sets
    every clock. `_thesis_clock_table` gives static 715/600/565/510 and RV 870/700/650/565 MHz
    (+18..+30% vs the 10-25 DSE's 570/490/470/425 and 670/570/540/480), so the 10-25 thesis_dse is
    stale: rebuild it at the new clocks. Registered operands now add only 1-3% (5-15 MHz); the tile
    set and the power run keep them (user 2026-10-26). RV/static clock ratio 1.22/1.17/1.15/1.11.
  - State: /nsim/mstrange/BUILDS/thesis_dse holds thesis_fmax (10-23) + regops (10-25),
    thesis_tiles_mem and the full thesis_dse (10-25) at static 570/490/470/425, RV 670/570/540/480
    MHz. lassen thesis 0f44a74 (Cond as an AND-OR select, 10-26) changes every PE's RTL (gen_rtl
    fetches lassen `thesis` at RTL time), so every PE probe, PE tile and app bundle before it is
    stale. MemTile RTL has no lassen, so the 10-25 MemTile builds only go stale if the re-probed
    clocks differ.
  - Order (`OUT=/nsim/mstrange/BUILDS/thesis_final`; gen_rtl also fetches lake, canal and gemstone,
    so hold RTL-affecting pushes to those and to lassen until the bundles and tiles are built):
    1. `--recipe thesis_fmax --out-dir $OUT --config-jobs 8 --zip --zip-slim` (20 synth probes)
    2. If the new table equals the old one, keep the 10-25 thesis_dse; else rebuild it below.
    3. `--recipe thesis_tiles --out-dir $OUT --clocks-from $OUT --rtl-only --config-jobs 8`, then the
       same without `--rtl-only`, with `--config-jobs 4 --zip --zip-slim` (config-jobs = PnRs)
    4. (if rebuilding) `--recipe thesis_dse ... --rtl-only --skip-existing --config-jobs 8`, then
       `--recipe thesis_dse --out-dir $OUT --clocks-from $OUT --config-jobs 6 --pnr-jobs 4
       --skip-existing --zip --zip-slim` (the zip holds all 246 configs; 248 before 2026-10-28)
    4b. `--recipe thesis_filter_ab --out-dir $OUT --clocks-from $OUT --rtl-only --config-jobs 8`,
       then the same without `--rtl-only`, with `--config-jobs 4 --zip --zip-slim` (10 PnR; its own
       dir thesis_filter_ab_mem and zip, so the lake tile_sweep ingest of the DSE zip stays clean:
       that ingest maps configs by spec values, not options, so ff8 rows would duplicate the DSE's)
    5. /aha: lake `python3 -m THESIS.apps.garnet_configs --commands` (lake THESIS/apps/
       CGRA_APP_POWER.md §2a) with GARNET_REV = the build machine's garnet; then
       `cgra_app_power.py --any-config --variants ... --clocks-from $OUT/thesis_tiles_pe/thesis_clocks.json
       --pe-registered-operands --replay-jobs 4 --zip` (§2b).
  - **One unattended command for steps 3-5 + both power runs (2026-10-28, session bc48e85f):**
    `bash mflowgen/thesis_final.sh` from the build machine's garnet (env knobs in its header).
    It pulls garnet + lake and checks everything in the foreground: probes in $OUT, garnet >=
    0bc94ef9/9573a704, both bundle tarballs whole (`gzip -t`, extracted once to $BUILDS), /sim/docker
    >= 20 GB free, recipe config counts 8/246/10, the clock table, and both power dry runs. Then it
    detaches (setsid nohup; log $OUT/thesis_final.log). Docker steps for every part go first
    (--rtl-only). Then the Innovus chain thesis_tiles_pe -> thesis_dse -> thesis_filter_ab (4 PnR;
    thesis_tiles_mem is dropped since its 2 configs are DSE PnR configs), one lighter retry per
    failed part, and only then the two power runs (user 2026-10-29: build results first). Then
    $OUT/thesis_final_summary.txt (statuses, exact replays, upstream lake/canal/gemstone/lassen tips at
    start vs end, zips) and $OUT/THESIS_FINAL_DONE. Re-running resumes. The whole flow was
    dry-run on /aha (DRY=1, fake layout). Bundles recorded later (e.g. the 6 static fw1/fw2 dp ones after
    clockwork 38ed931e) go in $BUILDS/app_bundles_thesis_dp_addon*.tgz (same root
    app_bundles_thesis_dp/<app>_agg/<config>). The next run extracts them
    once, and the resumed power run adds just those variants. Since 2026-10-28 late (session bc48e85f):
    - An add-on bundle that REPLACES one already in $B first deletes the old bundle directory
      (tar would leave its stray files) and that variant's `N-application-/testbench-/
      post-synth-power-<variant>` dirs in `$POWER_DP/<config>/Tile_*`. make would otherwise
      call the old replay up to date: the bundle path is a step param, not a make dependency.
      The next `mflowgen run` gives those steps new build ids (mflowgen keeps the others' ids).
    - A new variant directory in an add-on (addon2's `resnet_pond_agg`) joins `--variants`
      after the six known ones, so it never becomes a config's d_* reference.
    - `POWER_ONLY=1 bash mflowgen/thesis_final.sh` runs just the power track next to a running
      build track. It does no git pull and no recipe count check; log
      $OUT/thesis_final_power_only.log; done at $OUT/THESIS_FINAL_POWER_DONE.
    - Every power track holds $OUT/.thesis_final_power.lock. A run that would swap bundles
      refuses to start while a track holds it, and a full run's own power track steps aside
      (WARNING) when a POWER_ONLY one is going.
    - DRY=1 leaves add-ons unextracted.
    - Tested on /aha with stub sweep_specs/cgra_app_power: replace + new variant, both locks,
      concurrent and after.
    - **2026-10-29 (user):** no .md5 needed. Every tarball is checked with `gzip -t`; a `<tgz>.md5`
      beside it is still checked. App power always runs after the build track (the concurrent mode
      is gone). **Newest results at any time in `$OUT/latest/`:**
      - `<part>_latest_slim.zip` per part and `cgra_app_power_thesis_{dp,fp_ab}_latest.zip`, plus
        `STATUS.txt` (last step, configs done per part, power rows, zip times).
      - A publisher refreshes them every SNAPSHOT_MIN (30) min, and again right after each part
        or power run. It zips only what changed: a newer `.time_end` / `done.flag` /
        `results.csv`, or a power `.hier`.
      - Each refresh runs `sweep_specs.py --zip-only --zip-slim --zip-path` (or
        `cgra_app_power.py --report-only --zip --zip-path`, new). Both rewrite the part's CSVs
        from its workspaces, so `correlation.csv` / `memtile_power.csv` cover every config
        finished so far.
      - Both tools now write their CSVs and zips beside the final name and rename them into
        place, so a snapshot never collides with the live run.
      - One round at a time ($LATEST/.publish.lock), also across a main run and a POWER_ONLY run.
      - Checked: stub run order (rtl -> parts, each with a snapshot after it -> power -> final
        round), `gzip -t` on half a tarball, and a real `--zip-only` on the thesis_tiles_pe zip
        (CSV identical to the build machine's; 60 MB in 11 s).
  - gen_app_bundle refuses a bundle without "comparison passed": u16 apps on the dw8/dw32 points
    record only where their outputs still match the 16-bit gold (Halide-to-Hardware/CLAUDE.md "Test
    apps for other CGRA data widths"). A camera bundle on a bigger array has a bigger `array_tiles`,
    so compare its app_W, not array_W.
  - **Recorded 2026-10-26..28 (session 1fa8a391): 64/84 bundles + conv_3_3 fp_ab 6/6** (72/84 with the
    add-ons below). Packed as
    `/aha/sweep_out/app_bundles_thesis_dp.tgz` and `app_bundles_thesis_fp_ab.tgz` (plain .vcd inside;
    `STATUS.txt` in the root has the matrix). Lake THESIS 8b0f2edc snapshot, GARNET_REV 9573a704 plus
    d79e37b7's gen_app_bundle.py. Camera is on 28x16 everywhere (16x16 never placed). Harris and unsharp
    at dw32 need `--glb-tile-mem-size 256`: at 128 their 32-bit input (69-71 KB) overruns a 64 KB GLB bank
    and the testbench's GLB check stops `make sim` (exit 2). Camera sims take ~1h15m, and on fw2_dw32
    dp longer than gen_app_bundle's default `--test-timeout` 5400 (it was re-run with 10800).
  - **Add-ons (2026-10-28 late, 72/84 with them; final, user 2026-10-29)**, same root, in /aha/sweep_out with `.md5` beside each:
    - `app_bundles_thesis_dp_addon1.tgz`: 6 NEW static bundles on clockwork 38ed931e. These are fw1 dp
      gaussian/unsharp/harris/camera (the fw1 dp compile now passes the schedule to build_buffers;
      before, the MEMs were exact delay lines but the 9 compute taps were 1-5 cycles off) and fw2 dp
      dw16/dw32 resnet (TB fetch loop one word short). 38ed931e leaves the other 64 unchanged: a dw16
      audit by 43d74890, and 5 dw8/dw32 static recompiles with bitstreams and placements identical.
    - `app_bundles_thesis_dp_addon2.tgz` (GARNET_REV 607cf9c5, loop rule, 38 -> 32 padding registers)
      REPLACES the main set's 5 RV `resnet_agg/*_nofp_portcg_thesis_rv`. Kernels: fw4 11677 -> 11661 ns,
      fw2 11758 -> 11742 ns. thesis_final.sh drops the old bundles' replays when it extracts it (above).
      The old bundles are in the main .tgz. addon2 also ADDS `resnet_pond_agg` RV on the two 1-input
      points: 177,697 ns, 9 MEM + 20 PE, after 08555638's pack_ponds fix (9363ba60). Its app is the
      untracked H2H copy `probe_1fa8/resnet_pond` (the manifests' app label), NOT `pondspec_e2e/resnet`:
      the reduction is innermost and accumulates in the pond, output channels are a loop, the output is
      (x, y, w), and HL_TARGET has enable_ponds. Source copy:
      /aha/sweep_out/app_bundles_thesis_dp_sources/resnet_pond/. lake's appendix and registry list only
      pondspec_e2e/resnet.
    - `app_bundles_thesis_dp_addon3.tgz` (2026-10-29, GARNET_REV 35e23a53: the balancer models PE
      input FIFO pre-fill) REPLACES the main set's 4 RV `camera_pipeline_agg/*_nofp_portcg_thesis_rv`
      at dw16 (fw4 sp, fw2 dp, fw2 sp in1, fw1 dp; 28x16). Kernel 16,459 -> 12,364 ns on all 4 (static
      12,562), 211 -> 208 padding registers. Recorded in `apps/camera_pipeline_2x2` itself, one cell
      after another, so the manifests keep the replaced bundles' app label.
    - Static resnet_pond outputs all zeros there at tile 28 AND at tile=14 (43.7k cycles, so not the
      16-bit counters): OPEN_ISSUES clockwork/static-resnet-pond-zero-output (43d74890: clockwork
      refused the keep-pixel-loops pond route, so the pond restarted per pixel). Static can only run
      at tile=14 (tile 28 = 2352 px x 66 cycles, past the 16-bit counters). The user stopped the static
      fix on 2026-10-29 (issue closed unfixed) and chose no addon4: these 2 static cells stay gaps,
      addon2's tile-28 RV pair stays the resnet_pond_agg cells, and the RV tile=14 pair (both
      bit-accurate, 44,585 ns, 588 outputs) stays unpacked in
      /aha/sweep_out/app_bundles_thesis_dp_staging_t14/. resnet_agg itself cannot map on 1 input port
      (two MEM writers; refused at `aha map` since 38ed931e).
    - Recording pitfalls: a fresh tree clone at an older GARNET_REV lacks d79e37b7's gen_app_bundle
      (aha map: pond collateral 16 vs MEM 32 at dw32); copy gen_app_bundle.py from >= 25836273. The
      tree's garnet shows `-dirty` in the manifest because `make map` writes the app's width headers
      into its own garnet/headers (intended: private tree). The recording scripts need `LAKE` (the
      lake snapshot) and xcelium on PATH; a replacing re-record moves the old bundle aside first, so
      it must put it back when the new one fails (`/aha/sweep_out/record_camera_rv_addon3.sh`).
  - The 12 gaps left: static resnet on the 2 1-input points (above); expected u16-vs-16-bit-gold gaps,
    camera at dw32 S+R (1 value: a 16-bit wrap clamps to 0 in the gold, 255 on hardware), dw8 harris
    (457) and unsharp (40535), dw8 camera halide "Bad slice args".
- **thesis_tiles run (build machine 2026-10-28/29, zips `thesis_dse_mem_r8cad-gf12_20261028-181946_slim`
  + `thesis_tiles_pe_r8cad-gf12_20261029-000821_slim`, extracted in /aha/sweep_out/thesis_tiles_20261029).**
  Run from a garnet before d5489e0d (dw64 named fw2_dw64_sc8192). Clocks as the probe table (static
  715/600/565/510, RV 870/700/650/565 MHz). Both design-point MemTiles and 6 of 8 PE tiles PASS (PT
  setup WNS -11 to -98 ps, worst the RV dw32 PE, whose Innovus reg2reg is -138 ps). Both dw64 PE tiles
  FAIL: RV at init (IMPPTN-970, 345 pins for 341 tracks; edge-pin fit, garnet 7b746d92)
  and static at route (NRIG-76 filler gaps: fix-tap-gaps above). At HEAD those two are new names
  (fw4_dw64_sc16384), so a rebuild gets fresh workspaces; delete the two fw2_dw64 workspaces first,
  or their FAIL rows stay in thesis_tiles_pe's CSVs and zip.
- `THESIS_PART_DIRS`: thesis_tiles_mem, thesis_dse_reduced_mem and thesis_dse_mem all build in
  `<out>/thesis_dse_mem`, so a later part with `--skip-existing` (not `--fresh`) only builds what
  is missing. `THESIS_CLOCKED_PARTS` refuse to run without --clocks-from / --clock-mhz.
- `--clocks-from` (`_thesis_clock_table`): a thesis_fmax out dir (reads each part's results.csv
  + correlation.csv; limit = 1000 / (period - synth WNS); also takes extracted zips as subdirs) or
  a JSON `{"static": {"16": 490}, "rv": {...}}`; the table goes to `<part>/thesis_clocks.json`.
  Each thesis config gets `clock_mhz` (sweep-only key; per-config CLOCK_PERIOD / clock_period_PE).
- Reports: `correlation.csv` gains `tile_synth_fmax_mhz` / `tile_pnr_fmax_mhz` (1000 / (period -
  WNS), the per-build clock projection), `data_width` (sweep_meta.json, new builds), and fits per
  `<mode>_dw<N>` when it has 3 fit points (used before the mode's pooled fit). Each fit's val_*
  is its error on the held-out rows in its scope, so pooled vs per-width compare on the same tiles.

**thesis_dse full sweep result (2026-10-25; zip thesis_dse_mem_r8cad-gf12_20261025-173346_slim,
analysis /aha/sweep_out/thesis_dse_20261025/README.md).** 245/248 PASS at the probe clocks (synth WNS
>= 0 everywhere; PnR PT WNS -3..-92 ps, RV worst). Held-out PnR error of the per-(mode, width) fits:
total area <= 1.1%, logic <= 2.8%, active power <= 8.3%, idle power up to 22% (leave-one-out: idle
fits better pooled per mode, 8% mean / 38% max). Failures:
- `fw1_dw64_sc4096_sp_in1_out1_nofp_portcg_thesis_rv` (RV dw64 fit tile): Innovus init IMPPTN-970,
  345 pins on the LEFT side vs 341 tracks: the die's fixed 226-row height (left/right pins spread
  over the height; the earlier "too narrow" was wrong). RV dw64 then uses the pooled RV fit. Fixed
  2026-10-28: the floorplans grow the die when a side's pins don't fit ("Edge-pin fit" above).
- PnR-level active memtile power on fw4 dw8 and fw8 dw32 RV: one output never toggles in the
  signoff-netlist sim, which runs without SDF (`-notimingchecks`, library specify delays) on a
  post-CTS netlist; synth level passes. Likely a clock-tree race in that sim, not the design.
  Fixed 2026-10-28: the pnr sims annotate signoff's SDF and drive inputs at the SDC's arrival
  times ("MemTile idle/active power"); not yet re-run on gf12.
Static vs RV twins (115, synth): total area RV/static median 1.22, logic 1.58 (fw1 +57..+74%, fw2-8
+12..+32%), idle 2.48x, active 1.24x. Design point at PnR: 12,708 vs 13,627 um2 (+7.2%).

**RV comparison-network trim A/B: `--recipe thesis_cmptrim` (2026-10-25, session cfc4174c).**
lake's opt-in `rv_comparator_trim` (lake CLAUDE.md §6 "(d) Trimmed comparators": one-sided
comparators, 8-bit scalar + barrier bit, level select over levels 0..2; generic synthesis:
MemTile network -46%, pond network -32%). Spec set `thesis_cmptrim` = the RV design point
`fw4_dw16_sc4096_sp_in2_out2_vc2_nofp_portcg_thesis_rv` and the same with the trim
(`..._portcg_cmptrim_thesis_rv`; `_cmp_trim_tag` names a dict `_cmp<os|s8|bb|l3>`; static
specs refuse the key; `SPEC_DEFAULTS` has it, so the pair doesn't dedup). The RV pond takes
the trim from the MEM spec (`cgra/util_onyx.py` `with_mem_power_options(..., rv=True)`,
`SPEC_RV_OPTIONS`; checked on a 4x2 `--thesis rv` build: every comparator, MEM and pond,
trimmed), so the same pair builds the PE tile A/B. Parts: `thesis_cmptrim_mem` (PnR +
idle/active power) and `thesis_cmptrim_pe` (PnR), both clocked (`--clocks-from`); 4 builds.
Needs lake with the option at origin/THESIS. Test `test_thesis_cmptrim_recipe`,
`test_rv_pond_inherits_the_comparator_trim`.
**Not adopted (user decision 2026-10-26, relayed by bc48e85f):** the thesis RV fabric keeps the full
comparators, so this recipe was never run; it stays for a later A/B.

**First thesis_fmax PE probe (2026-10-23, zip thesis_fmax_pe_r8cad-gf12_20261023-055808_slim,
0.23 ns input budget, gated-pond PEs; extracted in /aha/sweep_out/thesis_fmax_20261023).** Synthesis
limits (1000 / (1 - WNS_ns)) and the clocks they give (0.9x, down to 5 MHz). Complete after the
RV dw32 rerun on gemstone thesis (zips thesis_fmax_{mem,pe}_r8cad-gf12_20261023-{152315,165134}_slim,
in .../rerun; their correlation.csv covers all 16, which is what --clocks-from reads). Every
MemTile (static + RV, all four widths) met 1000 MHz (WNS 0), so the PE sets every clock:

| dw | static PE | clock | RV PE | clock | RV clock vs static |
|---|---|---|---|---|---|
| 8 | 638 MHz | 570 | 749 MHz | 670 | +18% |
| 16 | 548 | 490 | 639 | 570 | +16% |
| 32 | 525 | 470 | 602 | 540 | +15% |
| 64 | 474 | 425 | 535 | 480 | +13% |

- **After the Cond rewrite (lassen 0f44a74; thesis_final probe 2026-10-27, Genus reports in
  /aha/sweep_out/thesis_fmax_20261027/zip).** Every PE path lost 277-318 ps (+18..30% clock). dw16 RV
  (1.28 ns): config reg -> RegisterMode mux 0.17 ns -> bf16 FPU add 0.76 ns (~60%) -> flag select
  0.16 ns -> Cond's AND-OR select 0.15 ns -> 1-bit output FIFO. dw16 static, registered operands
  (1.50 ns): operand reg -> FPU 0.79 ns -> flags + Cond 0.30 ns -> B1 SB mux / RMUX -> SB out,
  + the 0.24 ns TILE_O_DELAY_NS budget. Now the FPU (dw16) / integer multiplier (other widths) sets
  the clock; Cond's OR reduction is still a short serial chain (~0.1 ns). The note below is the
  pre-rewrite picture.
- **Where the time goes (2026-10-23, Genus reports of these probes).** Every PE's worst path, at
  every width, static and RV, ends at the 1-bit predicate output: operand (CB from the input
  budget on static; a constant config register or input FIFO on RV) -> RegisterMode mux -> ALU
  (dw 8/32/64: the dw x dw -> 2dw integer multiplier, an add and the zero flag; dw16: the bf16
  FPU add and its flags, slower than the 16-bit integer path) -> lassen `Cond` -> res_p -> static:
  the 1-bit SB register in the same tile / RV: the 1-bit output FIFO. ALU part 0.69 / 0.93 / 1.0 /
  1.2 ns at dw 8/16/32/64; Cond + output ~0.43 ns at every width. lassen `cond.py` is a 20-way
  if/elif, which synthesized into a serial chain of 19 Mux2xBit instances: with flatten-effort 0
  (thesis recipes, per-block area) each is its own module and Genus cannot rebalance it into a
  ~5-level tree. Not changed (user decision): let Genus flatten the PE (Tile_PE default 3), or
  rewrite Cond as a parallel compute + one select. MemTiles met 1 GHz everywhere; the paths that
  sat at the limit are config -> schedule/address generators (RV item-filter SGs, static port and
  SIPO/PISO SGs, stencil_valid SG) and RV SB ready -> valid. PnR at 400 MHz (2026-10-22, old
  budgets): MemTiles -3..-11 ps on pass-through/feedthrough budgets; static PE -38 ps on the same
  predicate path (SB in -> ALU -> 1-bit SB out); RV PE -64 ps on SB ready -> output fork gating ->
  SB valid (273 ps vs the fixed 210 ps sb_delay budget, independent of the clock).
- **The static-vs-RV clock gap is the input budget (2026-10-24, report
  https://claude.ai/artifact/Q4NmuZn3oZNK3mLDAzx9Dh; extraction + page generator in cfc4174c's
  scratchpad slow/{extract.py,build_report.py}).** Period gap 234 / 260 / 244 / 240 ps at dw 8/16/32/64,
  of which 230 ps is the upstream budget charged to static (its PE computes on inputs the same cycle);
  the datapath (ALU/FPU + condition logic) differs by <= 39 ps, front end and output side the rest.
  With d = 0 static is within 0.3-1.9% of RV. **But compiled static apps never use that path
  (found 2026-10-24):** MetaMapper's PipelinePEs (run unless PIPELINED=0, which only the RV flows set)
  puts every routed PE operand in lassen RegisterMode DELAY (decoded static thesis conv_3_3: all routed
  operands DELAY, constants CONST, none BYPASS). So the static tile STA times a bypass path apps don't
  use; the real static path starts at the operand register and the hop moves to the output side
  (est. dw16 ~1.58 ns with a first-hop SB register, ~ RV's 1.566). The static clocks derived from the
  bypass path (490 MHz at dw16) are pessimistic; a registered-operand constraint mode (false-path each
  RegisterMode value->O0, plus an output budget) is the fair one. Memory project_rv_tile_fifo_experiment.
  Built 2026-10-24: `--pe-registered-operands` (static thesis PEs only) -> env PE_OPERANDS_REGISTERED=1
  (Tile_PE constraints.tcl false-paths RegisterMode_inst*/value -> O0; errors if those pins are missing)
  and TILE_O_DELAY_NS = THESIS_O_DELAY_NS 0.24 (archipelago SB_IN_to_PE) on the SB outputs (common.tcl
  adds it back to the SB feedthrough budgets). `--recipe thesis_fmax_regops` (part thesis_fmax_pe_regops,
  spec set thesis_pe_widths_static, 4 synth probes) is also in `thesis_fmax`; `--clocks-from` lets a
  *regops* sweep replace the static PE limit; thesis_tiles_pe builds static PEs in this mode.
  **Result (zip thesis_fmax_pe_regops_r8cad-gf12_20261025-135014_slim, extracted in
  /aha/sweep_out/thesis_fmax_regops_20261025):** static limits 648 / 554 / 534 / 481 MHz at dw
  8/16/32/64 (bypass-path probe: 638 / 548 / 525 / 474), clocks 580 / 495 / 480 / 430 (+5..+10 MHz),
  so the static builds at the old clocks stand. The worst path is now operand register -> bf16 FPU add
  (dw16) -> serial Cond chain -> res_p -> B1 SB mux -> SB out at 1,565 ps, plus the 240 ps output
  budget = 1,805 ps. The PE logic is RV's (1.566 ns); the static-vs-RV gap is that output budget, i.e.
  the assumption that the PE output leaves the tile unregistered. Registering the first hop (an
  archipelago choice: a cycle of latency) would put static at RV's clock.
  Same report:
  PnR area by cell type and by matched block (Innovus signoff.area.rpt self areas, sums exact) and
  MemTile PT power by block/cell (power.cell; idle is mostly clock tree + gates, RV's extra idle is
  the tile port FIFOs), per-path-group worst paths (signoff_<group>.tarpt) on a block diagram.
- RV dw32 failed in Genus elaboration: "Unable to find port 'valid_in' of instance 'u_mux_logic' of
  module 'mux_logic_32_5'". gemstone's AOI mux named its inner modules precoder/mux_logic_<width>_
  <height> by width and height only, so at dw32 the RV data muxes and the plain 32-bit config muxes
  defined two different modules under one name (also mux_logic_32_2, precoder_32_2/5); Genus kept
  the one without valid ports. Simulators that keep the first definition ran it (a16b3973's dw32 RV
  apps passed). Only thesis RV at dw32 has the pair: RV data muxes are dw wide, the stock fabric's
  are dw+1.
- Fix: gemstone branch `thesis` c3f0acc (new personal branch; aha mek .gitmodules gemstone ->
  thesis): the first mux type to use a width/height keeps the plain names, any other type gets
  `_<type>` names (e.g. mux_logic_32_5_regularreadyvalid). Checked locally (PYTHONHASHSEED=0, old vs
  new gemstone): dw32 RV duplicates gone (diff = the 4 renamed modules + instances); Zircon 8x2,
  thesis dw16 RV/static and dw32 static identical under aha's vcompare (dw16 RV byte-identical).
  gen_rtl.sh fetches gemstone thesis in the container for thesis builds, like canal.
- A workspace whose rtl step ran with the old gemstone keeps its RTL: rebuild it with --fresh.

**gf12 `thesis_mem` results (2026-10-18 build, zip thesis_mem_r8cad-gf12_20261018-220554_slim,
extracted under /aha/sweep_out/thesis_mem_20261018).** Static vs RV MemCore tile, 4 KB spec,
1.333 ns clock, both PASS through PT signoff:
- **Area after PnR:** 13,114 vs 15,766 um2 (+20.2%). Logic is 7,489 vs 10,141 (+35%); the
  SRAM (2 x IN12LP_S1DB 512x32) is 5,625 in both.
- **Where RV's +2,632 um2 goes** (synthesis cell area):
  - lake controller 2,987 → 4,521 (+1,534);
  - switch-box registers: the 40 per tile become 2-deep FIFOs (+924);
  - switch-box config bits (+187);
  - MEM port FIFOs (+268);
  - switch-box ready/valid fan-in and muxing (about +150);
  - MemCore config (−470: static schedules have more config bits).
- **Timing:** setup WNS −6 ps static (config feedthroughs) vs −35 ps RV (68 failing paths:
  combinational switch-box `ready` → other tracks' `valid`, the lazy-fork gating).
- **Against the stock fabric** (clock_gating_ab_20261018 baseline: 14,960 static / 15,888 RV
  after PnR), the thesis static tile is 12% smaller and the RV tile about equal. The real
  static-vs-RV gap is 20%, not 6%.
- **Caveats:**
  - Built before canal `fifo_only_regs` (2026-10-19): a rebuild drops each RV switch-box
    register's `fifo_en` bit, estimated at 60-70 um2.
  - Both tiles keep the power-domain OR (27 um2), since the thesis flow does not apply
    `--no-pd`.
  - No power: that build stopped at timing signoff. Since 2026-10-21 the thesis MemTile
    recipes also run `--memtile-power` (below).

**`--recipe thesis_mem_opt` (2026-10-20, user request): the thesis MemTile with lake's
area/power options, 3 builds through PT signoff** (spec set `thesis_fabric_opt`, preset
`thesis_opt_pnr`; not part of `thesis_fabric`):
- `..._sharectr_portcg_thesis`: static, shared cycle counter + per-port clock gating;
- `..._ff8_portcg_thesis_rv`: RV, per-port gating, filter path as an 8-deep FIFO;
- `..._nofp_portcg_thesis_rv`: RV, per-port gating, no filter path (new sweep knob
  `add_filter_path=False`, name `_nofp`; RV only).

One static tile serves both RV comparisons, because the static spec has no filter path.
The RV tiles also get FIFO-only switch-box registers (canal thesis, fetched in the rtl
container).

Checked locally (gen_rtl flags + `--thesis`, 4x2, private lake THESIS de6b95c5 + canal
2f06aeb):
- all three RTLs build;
- static has `shared_clk_ctr` and 4 port gates;
- RV FIFO-8 has 6 gated ports and fewer filter config registers than plain RV;
- RV no-filter-path has 4 gated ports and no filter-port CB;
- no `fifo_en` anywhere.

Command:
`./mflowgen/sweep_specs.py --recipe thesis_mem_opt --out-dir /nsim/mstrange/BUILDS/sweep_out/thesis_opt --zip --zip-slim`.
`--recipe thesis_opt` = `thesis_mem_opt` + `thesis_pe` (5 builds, each part into its own
subdirectory and zip). The PE tile takes none of these options: they are MEM spec knobs.

**Idle/active MemTile power on the thesis tiles (2026-10-21, session cfc4174c).**
`memtile-power-test-gen` builds `ThesisGarnet` when the step's `thesis` parameter (the tile
graph's THESIS_FABRIC) is set, passes `--thesis`, and in the container fetches canal
`thesis` as gen_rtl does. `thesis_mem` and `thesis_mem_opt` now include `--memtile-power`;
the PE part has no idle/active test (app power only).
- **Checked locally on five thesis tiles** (4x2, `--use_sim_sram`, RTL sims with the step's
  cmd.tcl): static, static with gating, RV, RV + gating + FIFO-8, and RV + gating + no
  filter path.
  - Idle and active PASS on all five, with a SAIF each.
  - Outputs change 981/980 times in 1000 cycles on static, 976/975 on RV (stock tiles: the
    same).
  - Gated ports: every `port_<i>_gclk` toggles 0 times in idle and 1999 in active; the
    FIFO-8 tile's filter ports stay gated in active (the program leaves them unused).
- **A thesis build made without `--memtile-power` can't simply be topped up.** The power
  steps change the graph (step numbers), so add power with a fresh build.

**App bundles and whole-CGRA power on the thesis fabrics (2026-10-21, session cfc4174c).**
- **Recording:** `gen_app_bundle.py --config <name>_thesis[_rv]` (or `--thesis`) records on the
  thesis CGRA:
  - `garnet.py` and `aha pnr` get `--thesis <mode>`;
  - RV runs with DENSE_READY_VALID only (no EXHAUSTIVE_PIPE), so `aha pnr` latency-matches by
    default and `aha test` starts flush-first;
  - `--rv-balance` is refused there (it is for EXHAUSTIVE_PIPE fabrics);
  - manifest.json gets `thesis: <mode>`.
- **Replaying:** `cgra_app_power.py` sets THESIS_FABRIC for both tile graphs from the manifest,
  and the spec for Tile_PE in both modes (garnet.py --thesis needs it). Variants must agree on
  `thesis`.
- **Checked locally:** conv_3_3 on the 8x8 thesis CGRA (`--cgra-tiles`).
  - Static: 4149 ns. RV: 4150 ns, balanced with 10 padding registers, flush-first.
  - Every recorded tile replays exactly at RTL (generate_testbench + the
    cadence-xcelium-sim flags, `+define+NO_SDF`, the bundle's garnet.v): 36 static tiles
    (7 MemCore + 29 PE) and 30 RV (5 + 25), 0 mismatches.
  - generate_testbench.py needed no change for thesis tiles (static ones have no
    ready/valid).
- Tests: test_app_bundle_guards `test_gen_app_bundle_thesis_config`,
  `test_cgra_app_power_thesis_bundle_tiles`.

Why RV runs slower than static in the matrix (2026-10-18; data: archipelago/CLAUDE.md "RV
without EXHAUSTIVE_PIPE"):
- Reconvergent forks (conv, gaussian, unsharp, harris): the RV flow balances nothing
  (MATCH_BRANCH_DELAY=0) and EXHAUSTIVE_PIPE turns route-length differences into stage
  differences. A lazy fork + 2-deep FIFOs runs a join at (short branch's buffer slots) /
  (long branch's round trip): conv 0.75 token/cycle (4149/0.75 = 5533), harris 0.107. With
  latency matching on the same placement and routing, RV = static: conv 4153 / 4149, gaussian
  6393 / 6389, unsharp 17480 / 17470, harris 17838 / 17816 (`aha pnr --rv-balance`, "RV branch
  balancing" above).
- Loop-carried recurrence (matmul_rvtry3, same in every pipelining mode): one scalar
  accumulator in the pond (address stride 0; 256 outputs of 16 dependent steps). The static
  schedule issues a step every 2 cycles (pond cycle stride [2, 34]: 34 cycles per output, 256 x
  34 + 556 = 9260). The RV pond -> PE -> pond loop takes 3 per step, so about 50 per output
  (256 x 50 + 555 = 13355): one more register stage (inferred: the RV PE's output FIFO).
  Structural RV cost on short recurrences; interleaving >= 3 accumulators would hide it.
  (Corrected 2026-10-18: this said 8192 + 1068, which ignored the 2 cycles per output.)

Tile_PE timing (local Genus 20.11 freepdk45, 1.333 ns, steady state: config regs
false-pathed, flush/stall 0; scratchpad thesis/synth): static worst R2R 3355 ps (pond addr ->
CB -> ALU -> 1-bit res_p -> SB mux -> SB reg; 16-bit data path ~3035), RV 2896 ps (input FIFO
rd_ptr -> ALU -> 1-bit output FIFO; 16-bit ~2624); old builds with the bypass case-analyzed:
3611 / 3270. Area 37.0k / 47.7k um2 (old ~50-55k / 54-61k). x0.53 -> gf12 synth ~1.78 ns
(static) / ~1.53 ns (RV). The worst path is on the PE's 1-bit result (compare/flag -> Cond):
RV apps use 1-bit nets only for compare results (RV harris 17-34 nets; conv/gaussian/unsharp
none); static also routes the output valid (stencil_valid -> IO).

## Build-machine note

The sweep runs from a **standalone** garnet checkout at
`/sim/mstrange/BUILD_CGRA/garnet` (with a sibling `lake`). aha gitlink bumps
do NOT update it — `git pull` there directly. Lake fixes flow via
origin/THESIS (gen_rtl checks it out in-container). Keep `sweep_out` out of
that checkout (docker-cp symlink breakage). See memory
`project_build_machine_standalone_garnet`. **Every new output goes under
`/nsim/mstrange/BUILDS/`** (rule since 2026-10-14: the `/sim` build disk is
full); the checkout itself stays on `/sim`.

### Build machine: stock-fabric thesis data runs (queued 2026-10-17)

Run these from `/sim/mstrange/BUILD_CGRA/garnet` after `git pull`, in this order.
What each part builds is in "Thesis data recipe" above. The current dw16 memory-tile
sweep (`NEW_SWEEP_r8cad-gf12_20261009-213941`) and the dw 8/32/64 sweep (2026-10-14)
are what the thesis uses now. Both were built with power domains (see "Power domains":
`--no-pd` was a no-op until 6f110058), and new builds have none. Step 2 rebuilds the
memtile part's PnR configs on current branches; the full part reproduces the rest.
The thesis-fabric runs (the results the thesis will use) are under "Thesis design-space
sweep". The static-fabric smoke test and the `fabric_mem` / `pe_tile` runs that were
steps 1-2 here are gone: `--dense-only` crashes (see "Thesis data recipe").

1. **App power.** First copy `/aha/sweep_out/app_bundles_dw16_20261014.tgz` over (the
   user does this; the build machine can't reach /aha). Extract it so that
   `<dir>/<app>/<config>/manifest.json` exists, then:

       ./mflowgen/sweep_specs.py --recipe app_power --out-dir /nsim/mstrange/BUILDS/thesis_data \
           --app-bundles /nsim/mstrange/BUILDS/app_bundles_dw16_20261014 --zip

   Its RV bundles were recorded without `--rv-balance`. Their power is valid, but
   their cycle counts include branch imbalance (see "RV branch balancing"). The LI
   performance figures need RV bundles re-recorded on /aha with `--rv-balance 8`.
2. **The synth->PnR model at every width (user request 2026-10-17; from scratch on
   current branches, 2026-10-18).** The 2026-10-14 sweep synthesized all 24 dw 8/32/64
   configs but ran PnR on only 6, and the dw16 fit (which overestimates dw8 power and
   underestimates dw64) projected the rest. Preset `memtile_pnr` builds the 12 dw16 fit
   and held-out configs and all 24 dw 8/32/64 configs through PnR into
   `<out-dir>/memtile`. The dw 8/32/64 configs are held out of the dw16 fit, so
   `pnr_validation.csv` gives its error at each width, and everything is built on one set of
   branches without power domains. Step 3's `--skip-existing` reuses them. They are all in
   the recipe's `--pnr-set`, so `--pnr-jobs` sets the parallelism (keep the machine's total
   PnR jobs near 6):

       ./mflowgen/sweep_specs.py --recipe memtile --preset memtile_pnr \
           --out-dir /nsim/mstrange/BUILDS/thesis_data --pnr-jobs 6 --rtl-only
       ./mflowgen/sweep_specs.py --recipe memtile --preset memtile_pnr \
           --out-dir /nsim/mstrange/BUILDS/thesis_data --pnr-jobs 4 --zip --zip-slim

   The first command makes only the two docker steps (rtl, memtile-power-test-gen) for all
   36 configs, a few minutes each. The second needs no docker. Run it on 2026-10-19
   (`memtile_r8cad-gf12_20261019-054400_slim`, single command): the 8 `dw16_fit8` configs
   passed PnR, with power on 4 (fw1 sc4096 and fw4 sc8192, static + RV). `/sim/docker` filled
   up at about 04:09: 28 RTL steps and 4 power test-gens failed at `docker run`. Analysis is
   in `/aha/sweep_out/memtile_pnr_20261019/README.md`. **Re-run 2026-10-19/21 with `--fresh`:
   36/36 PASS** (zip `memtile_r8cad-gf12_20261021-031739_slim`; result under "dw 8/32/64
   Tile_MemCore PPA").

3. **Everything from scratch** (the memtile part is 196 configs, 36 of them through
   PnR, about 2 days at `--pnr-jobs 2`). `--skip-existing` reuses what steps 1-2 built:

       ./mflowgen/sweep_specs.py --recipe thesis --out-dir /nsim/mstrange/BUILDS/thesis_data \
           --app-bundles /nsim/mstrange/BUILDS/app_bundles_dw16_20261014 \
           --config-jobs 4 --pnr-jobs 2 --zip --zip-slim --skip-existing

Copy the zips back to the user. The SRAM datasheets inside them are under NDA: don't
commit or upload them. lake can ingest only the memtile zip so far.
Record each run's result here: date, zip name, pass/fail, and anything that broke.

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
