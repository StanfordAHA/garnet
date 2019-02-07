io_core functional model tests and magma tests
It is not able to run regression test using FunctionalTester in fault because io_core does not have clk input, whereas FunctionalTester class always requires clk input.
It seems okay, though, because io_core is really simple and we only need it for place and route.
