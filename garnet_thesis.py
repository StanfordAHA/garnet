"""Thesis CGRA builds: garnet.py --thesis {static,rv}.

A static-dense and a ready-valid-dense CGRA that differ only in what their execution
model needs (cgra/util_thesis.py has the hardware). The GLB, the global controller and
place-and-route / bitstream generation are garnet.py's: ThesisGarnet replaces only the
CGRA fabric of the Garnet top.

    python garnet.py --thesis static --lake-spec-config spec.json --width 16 --height 16 -v
    python garnet.py --thesis rv     --lake-spec-config spec.json --width 16 --height 16 -v

Apps: a static fabric runs static apps (DENSE_READY_VALID unset at every stage), an rv
fabric runs dense ready-valid apps (DENSE_READY_VALID=1 at every stage). Use the same
flags (and --thesis) for aha pnr as for the RTL: the bitstream comes from the fabric
model garnet.py builds.
"""
import os

from gemstone.generator.generator import Generator

from garnet import Garnet


class ThesisGarnet(Garnet):
    def __init__(self, args, io_sides):
        Generator.__init__(self)

        mode = args.thesis
        assert mode in ("static", "rv"), mode
        if args.dense_only:
            raise ValueError("--thesis builds its own fabric; drop --dense-only")
        for flag in ("using_matrix_unit", "include_E64_hw", "include_multi_bank_hw",
                     "include_mu_glb_hw", "virtualize", "amber_pond", "give_north_io_sbs"):
            if getattr(args, flag, False):
                raise ValueError(f"--thesis does not support --{flag.replace('_', '-')}")
        if args.num_fabric_cols_removed:
            raise ValueError("--thesis does not support --num-fabric-cols-removed")
        if not os.environ.get("LAKE_SPEC_CONFIG"):
            raise ValueError("--thesis needs --lake-spec-config")
        if args.lake_spec_mode and args.lake_spec_mode != mode:
            raise ValueError(f"--lake-spec-mode {args.lake_spec_mode} contradicts --thesis {mode}")
        # The lake spec MemCore and pond follow the fabric's mode
        os.environ["LAKE_SPEC_MODE"] = mode
        if mode == "rv":
            # Switch-box FIFOs: the RegFIFO (one 2-deep FIFO), as every lake-spec build
            os.environ["USE_NON_SPLIT_FIFOS"] = "1"
        self.thesis_mode = mode

        if args.standalone:
            assert args.interconnect_only

        self.glb_params = args.glb_params
        self.config_addr_width = 32
        self.config_data_width = 32
        self.amber_pond = False

        args.tile_id_width = 16
        args.config_addr_reg_width = 8
        args.config_data_width = self.config_data_width

        self.ready_valid = mode == "rv"
        # Data tracks are data_width bits in both fabrics (ready/valid are separate wires)
        self.data_width = args.glb_params.cgra_data_width
        self.data_track_width = self.data_width
        self.width = args.width
        self.height = args.height

        self.mu_oc_0 = 0
        self.num_fabric_cols_removed = 0

        self.pe_fc = args.pe_fc
        self.harden_flush = args.harden_flush
        self.pipeline_config_interval = args.pipeline_config_interval

        self.io_sides = io_sides
        self.include_E64_hw = False
        self.include_multi_bank_hw = False
        self.include_mu_glb_hw = False
        self.pipeline_mu2cgra = False

        if not args.interconnect_only:
            self.build_glb()

        print(f"- BUILD THE THESIS CGRA ({mode})")
        from canal.util import SwitchBoxType
        from cgra.util_thesis import create_cgra_thesis
        self.interconnect = create_cgra_thesis(
            mode, args.width, args.height, io_sides,
            num_tracks=args.num_tracks,
            mem_ratio=(1, args.mem_ratio),
            use_sim_sram=args.use_sim_sram,
            dual_port=args.dual_port,
            add_pond=not args.no_pond,
            harden_flush=args.harden_flush,
            standalone=args.standalone,
            pipeline_config_interval=args.pipeline_config_interval,
            switchbox_type={"Imran": SwitchBoxType.Imran, "Disjoint": SwitchBoxType.Disjoint,
                            "Wilton": SwitchBoxType.Wilton}[args.sb_option],
            pipeline_regs_density=args.pipeline_regs_density,
            port_conn_option=args.port_conn_option)

        from passes.interconnect_port_pass import stall_port_pass, config_port_pass
        stall_port_pass(self.interconnect, port_name="stall", port_width=1, col_offset=1)
        if self.harden_flush:
            stall_port_pass(self.interconnect, port_name="flush", port_width=1,
                            col_offset=args.glb_params.num_cols_per_group, pipeline=True, io_sides=io_sides)
        config_port_pass(self.interconnect, pipeline=args.config_port_pipeline)

        self.inter_core_connections = {}
        for bw, interconnect in self.interconnect._Interconnect__graphs.items():
            self.inter_core_connections[bw] = interconnect.inter_core_connection

        if not args.interconnect_only:
            # dense_only selects the 16-bit matrix-unit IO, unused here
            self.build_glb_ports(args.glb_params, False, args.mu_datawidth, not self.ready_valid, 0, 0)
        else:
            self.lift_ports(self.width, self.config_data_width, self.harden_flush)

    def check_app_mode(self):
        """A static fabric runs static apps, an rv fabric dense ready-valid apps."""
        drv = os.environ.get("DENSE_READY_VALID") == "1"
        if drv != (self.thesis_mode == "rv"):
            raise ValueError(f"--thesis {self.thesis_mode} fabric needs DENSE_READY_VALID "
                             f"{'=1' if self.thesis_mode == 'rv' else 'unset'} (map, pnr and test)")

    def load_netlist(self, *args, **kwargs):
        # The netlist's data buses are data_width bits (no end-of-stream bit)
        from mapper.netlist_util import set_rv_track_eos_bit
        set_rv_track_eos_bit(False)
        return super().load_netlist(*args, **kwargs)

    def place_and_route(self, args, load_only=False):
        self.check_app_mode()
        return super().place_and_route(args, load_only=load_only)
