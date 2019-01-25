# Test Plan

## Designers own tests
All new HW (RTL) must be submitted to the design repository using a PR.

Reviewers are responsible for enforcing that:
* New code is accompanied by tests with good coverage (designer should explain
  why the tests they have included are sufficient)
* Bug fixes are accompanied by a test for the specific bug

PR's will automatically run checks for functional verification and virtual
tapeout.  All new RTL should have 90% or higher statement coverage (verilog).

## JTAG (Global Controller)
Smoke testing the CGRA will be done using the JTAG. If the JTAG does not work,
the chip cannot be configured and is therefor unuseable. The JTAG should have a
comprehensive set of unit tests that verify that an external entity can read
and write the JTAG registers.  These unit tests should be written using fault,
so it can be used both for functional verification as well as bringup.  Fault
will be responsible for generating the SVF files for bringing up the JTAG
(using the same code for the functional verification).

## Interconnect
Once the JTAG functionality has been verified, there will be a suite of tests
to verify the functionality of the interconnect. The interconnect should be
unit tested in isolation (manually setting the configuration register values)
as well as with the JTAG (using a driver to serialize the configuration
commands).  These tests should use boundary scan techniques to verify
the functionality of the interconnect.

## PE
Unit tests should cover all specified operations and configuration state of the
module.

## Memory
Unit tests should cover all specified modes of the memory.  It is important to
generate complex sequences of interactions to test the memory behavior, such as
random interleavings of reads and writes.

## Applications
With all the system components unit tested and integration tested, all available 
application bitstreams and reference implementations should be used to verify
the functionality of the chip and supporting software at a system level.

## TODO
* Stall network
* Clock/Power domains
