#ifndef RDAI_CLOCKWORK_PLATFORM_H
#define RDAI_CLOCKWORK_PLATFORM_H

#include "rdai_api.h"

extern RDAI_Platform rdai_clockwork_platform;

static RDAI_Device aha_halide_hardware_pointwise_1 = {
	{ 1 },
	{
		{ "aha" },
		{ "halide_hardware"  },
		{ "pointwise" },
		1,
	},
	&rdai_clockwork_platform,
	NULL,
	1
};

static RDAI_Device *rdai_clockwork_platform_devices[2] = { &aha_halide_hardware_pointwise_1, NULL };

RDAI_Platform rdai_clockwork_platform = {
	RDAI_PlatformType::RDAI_CLOCKWORK_PLATFORM,
	{ 0 },
	NULL,
	rdai_clockwork_platform_devices
};


#endif // RDAI_CLOCKWORK_PLATFORM_H
