from abc import abstractmethod
import copy


class SideModel:
    def __init__(self, num_tracks, layers):
        self.num_tracks = num_tracks
        self.layers = layers

        self.values = {l: [0 for _ in range(self.num_tracks)]
                       for l in self.layers}

    def __str__(self):
        return str(self.values)


class SimpleSBComponent:
    SIDES = ("north", "west", "south", "east")

    def __init__(self, num_tracks, layers, num_core_outputs):
        self.num_tracks = num_tracks
        self.layers = layers
        self.num_core_outputs = num_core_outputs

    # NOTE(rsetaluri): We are overloading SideModel to mean both the set of
    # input values, as well as the configuration value for each track (because
    # the number of config registers is equal to the total number of tracks).
    @abstractmethod
    def confiure(self, sides_config):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def __call__(self, in_, core_outputs):
        pass

    # A utility function that takes in a functor and allows iteration over each
    # track in a "tile", that is for each side, layer, and track, we call `fn`
    # with those arguments.
    def iterate(self, fn):
        for side in SimpleSBComponent.SIDES:
            for layer in self.layers:
                for track in range(self.num_tracks):
                    fn(side, layer, track)

    # A utility function that allows creation of a dictionary mapping all side
    # strings to an empty side model (filled with zeros).
    def make_sides(self):
        return {side: SideModel(self.num_tracks, self.layers) for
                side in SimpleSBComponent.SIDES}


class SimpleSBModel(SimpleSBComponent):
    def __init__(self, num_tracks, layers, num_core_outputs):
        super().__init__(num_tracks, layers, num_core_outputs)

        self.out = self.make_sides()
        self.sides_config = self.make_sides()

    def reset(self):
        # Initialize all config registers back to zero.
        self.sides_config = self.make_sides()

    def configure(self, sides_config):
        self.sides_config = copy.deepcopy(sides_config)

        # Check that user has not tried to use buffered muxes
        def _fn(side, layer, track):
            config = self.sides_config[side].values[layer][track]
            if config[1] != 0:
                # output is configured as buffered
                # not supported by this model
                raise NotImplementedError
        self.iterate(_fn)

    def __call__(self, in_, core_outputs):
        if len(core_outputs) != self.num_core_outputs:
            raise ValueError("Wrong number of core outputs",
                             core_outputs, self.num_core_outputs)

        assert in_.keys() == self.out.keys()
        for side in in_.values():
            assert side.num_tracks == self.num_tracks
            assert side.layers == self.layers

        # For each side, layer, and track determine the output. It is basically
        # mux([inputs], sel), where [inputs] is the "other" sides for the same
        # layer and track + the appropriate core output, and sel comes from the
        # configuration.
        def _fn(side, layer, track):
            inputs = []
            for other_side in SimpleSBComponent.SIDES:
                if other_side == side:
                    continue
                inputs.append(in_[other_side].values[layer][track])
            # TODO(rsetaluri): Abstract this part out. Right now it is a
            # hard coded hack.
            inputs.append(core_outputs["data_out_16b"] if layer == 16
                          else core_outputs["data_out_1b"])
            select = self.sides_config[side].values[layer][track][0]
            self.out[side].values[layer][track] = inputs[select]

        self.iterate(_fn)


# TODO(rsetaluri): Move this class into a common file.
class TesterBase:
    def __init__(self, model, tester):
        self.model = model
        self.tester = tester
        self.circuit = self.tester.circuit


class SimpleSBTester(SimpleSBComponent, TesterBase):
    def __init__(self, num_tracks, layers, num_core_outputs, model, tester):
        SimpleSBComponent.__init__(self, num_tracks, layers, num_core_outputs)
        TesterBase.__init__(self, model, tester)

    def configure(self, sides_config):
        self.model.configure(sides_config)

        # TODO(rsetaluri): Move this function out.
        def _impl(addr, data):
            # Perform config write.
            self.tester.poke(self._circuit.clk, 0)
            self.tester.poke(self._circuit.reset, 0)
            self.tester.poke(self._circuit.config.config_addr, addr)
            self.tester.poke(self._circuit.config.config_data, data)
            self.tester.poke(self._circuit.config.read, 0)
            self.tester.poke(self._circuit.config.write, 1)
            self.tester.step(2)
            # Perform config read and issue expect.
            self.tester.poke(self._circuit.config.write, 0)
            self.tester.poke(self._circuit.clk, 0)
            self.tester.poke(self._circuit.reset, 0)
            self.tester.poke(self._circuit.config.config_addr, addr)
            self.tester.poke(self._circuit.config.read, 1)
            self.tester.poke(self._circuit.config.write, 0)
            self.tester.poke(self._circuit.config.read, 0)
            self.tester.step(2)
            self.tester.expect(self._circuit.read_config_data, data)

        idx = 0

        def _fn(side, layer, track):
            nonlocal idx
            _impl(idx, sides_config[side].values[layer][track][0])
            idx += 1
            _impl(idx, sides_config[side].values[layer][track][1])
            idx += 1

        self.iterate(_fn)

    def reset(self):
        self.tester.poke(self._circuit.reset, 1)
        self.tester.eval()
        self.tester.poke(self._circuit.reset, 0)

    def __call__(self, in_, core_outputs):
        self.model(in_, core_outputs)

        # Poke values based on the core outputs.
        for name, value in core_outputs.items():
            port = self._circuit.interface.ports[name]
            self.tester.poke(port, value)

        # Poke the circuit with the input values.
        def poke(side, layer, track):
            in_port = getattr(self._circuit.interface.ports[side].I,
                              f"layer{layer}")[track]
            self.tester.poke(in_port, in_[side].values[layer][track])
            self.tester.eval()

        # Check that the circuit output matches the model.
        def expect(side, layer, track):
            expected = self.model.out[side].values[layer][track]
            out_port = getattr(self._circuit.interface.ports[side].O,
                               f"layer{layer}")[track]
            self.tester.expect(out_port, expected)

        self.iterate(poke)
        self.iterate(expect)
