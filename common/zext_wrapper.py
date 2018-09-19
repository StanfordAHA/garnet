import magma
import generator.generator as generator


class ZextWrapper(generator.Generator):
    def __init__(self, in_width, out_width):
        super().__init__()

        if out_width <= in_width:
            raise ValueError(f"output width must be greater than input width "
                             f"(output width = {out_width}, input width = "
                             f"{in_width})")

        self.in_width = in_width
        self.out_width = out_width

        self.add_ports(
            I=magma.In(magma.In(magma.Bits(self.in_width))),
            O=magma.Out(magma.Out(magma.Bits(self.out_width))),
        )

    def circuit(self):
        diff = self.out_width - self.in_width

        class _ZextWrapperCircuit(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                magma.wire(magma.zext(io.I, diff), io.O)

        return _ZextWrapperCircuit

    def name(self):
        return f"ZextWrapper_{self.in_width}_{self.out_width}"
