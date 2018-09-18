import magma
import generator.generator as generator


class CoreirWrap(generator.Generator):
    def __init__(self, out_type, in_type, type_name):
        super().__init__()

        self.out_type = out_type
        self.in_type = in_type
        self.type_name = type_name

        self.add_ports(
            I=magma.In(self.in_type),
            O=magma.Out(self.out_type),
        )

    def circuit(self):
        def sim_wrap(this, value_store, state_store):
            input_val = value_store.get_value(getattr(this, "in"))
            value_store.set_value(this.out, input_val)

        Wrapper = magma.DeclareCircuit(
            f'coreir_wrap{self.type_name}',
            "in", magma.In(self.in_type), "out", magma.Out(self.out_type),
            coreir_genargs={"type": self.out_type},
            coreir_name="wrap",
            coreir_lib="coreir",
            simulate=sim_wrap,
        )

        class _CoreirWrapCircuit(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                wrapper = Wrapper()
                magma.wire(io.I, wrapper.interface.ports["in"])
                magma.wire(wrapper.out, io.O)

        return _CoreirWrapCircuit

    def name(self):
        return f"CoreirWrap_{self.in_type}_{self.out_type}_{self.type_name}"
