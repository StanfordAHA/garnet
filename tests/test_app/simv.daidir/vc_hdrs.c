#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <dlfcn.h>
#include "svdpi.h"

#ifdef __cplusplus
extern "C" {
#endif

/* VCS error reporting routine */
extern void vcsMsgReport1(const char *, const char *, int, void *, void*, const char *);

#ifndef _VC_TYPES_
#define _VC_TYPES_
/* common definitions shared with DirectC.h */

typedef unsigned int U;
typedef unsigned char UB;
typedef unsigned char scalar;
typedef struct { U c; U d;} vec32;

#define scalar_0 0
#define scalar_1 1
#define scalar_z 2
#define scalar_x 3

extern long long int ConvUP2LLI(U* a);
extern void ConvLLI2UP(long long int a1, U* a2);
extern long long int GetLLIresult();
extern void StoreLLIresult(const unsigned int* data);
typedef struct VeriC_Descriptor *vc_handle;

#ifndef SV_3_COMPATIBILITY
#define SV_STRING const char*
#else
#define SV_STRING char*
#endif

#endif /* _VC_TYPES_ */

#ifndef __VCS_IMPORT_DPI_STUB_parse_metadata
#define __VCS_IMPORT_DPI_STUB_parse_metadata
__attribute__((weak)) void* parse_metadata(/* INPUT */const char* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */const char* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(const char* A_1)) dlsym(RTLD_NEXT, "parse_metadata");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "parse_metadata");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_parse_metadata */

#ifndef __VCS_IMPORT_DPI_STUB_get_place_info
#define __VCS_IMPORT_DPI_STUB_get_place_info
__attribute__((weak)) void* get_place_info(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1)) dlsym(RTLD_NEXT, "get_place_info");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_place_info");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_place_info */

#ifndef __VCS_IMPORT_DPI_STUB_get_bs_info
#define __VCS_IMPORT_DPI_STUB_get_bs_info
__attribute__((weak)) void* get_bs_info(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1)) dlsym(RTLD_NEXT, "get_bs_info");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_bs_info");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_bs_info */

#ifndef __VCS_IMPORT_DPI_STUB_get_input_info
#define __VCS_IMPORT_DPI_STUB_get_input_info
__attribute__((weak)) void* get_input_info(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_input_info");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_input_info");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_input_info */

#ifndef __VCS_IMPORT_DPI_STUB_get_output_info
#define __VCS_IMPORT_DPI_STUB_get_output_info
__attribute__((weak)) void* get_output_info(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_output_info");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_output_info");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_output_info */

#ifndef __VCS_IMPORT_DPI_STUB_glb_map
#define __VCS_IMPORT_DPI_STUB_glb_map
__attribute__((weak)) int glb_map(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "glb_map");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "glb_map");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_glb_map */

#ifndef __VCS_IMPORT_DPI_STUB_get_num_groups
#define __VCS_IMPORT_DPI_STUB_get_num_groups
__attribute__((weak)) int get_num_groups(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_num_groups");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_num_groups");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_num_groups */

#ifndef __VCS_IMPORT_DPI_STUB_get_group_start
#define __VCS_IMPORT_DPI_STUB_get_group_start
__attribute__((weak)) int get_group_start(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_group_start");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_group_start");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_group_start */

#ifndef __VCS_IMPORT_DPI_STUB_get_num_inputs
#define __VCS_IMPORT_DPI_STUB_get_num_inputs
__attribute__((weak)) int get_num_inputs(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_num_inputs");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_num_inputs");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_num_inputs */

#ifndef __VCS_IMPORT_DPI_STUB_get_num_io_tiles
#define __VCS_IMPORT_DPI_STUB_get_num_io_tiles
__attribute__((weak)) int get_num_io_tiles(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_num_io_tiles");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_num_io_tiles");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_num_io_tiles */

#ifndef __VCS_IMPORT_DPI_STUB_get_num_outputs
#define __VCS_IMPORT_DPI_STUB_get_num_outputs
__attribute__((weak)) int get_num_outputs(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_num_outputs");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_num_outputs");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_num_outputs */

#ifndef __VCS_IMPORT_DPI_STUB_get_placement_filename
#define __VCS_IMPORT_DPI_STUB_get_placement_filename
__attribute__((weak)) SV_STRING get_placement_filename(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static SV_STRING (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (SV_STRING (*)(void* A_1)) dlsym(RTLD_NEXT, "get_placement_filename");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_placement_filename");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_placement_filename */

#ifndef __VCS_IMPORT_DPI_STUB_get_bitstream_filename
#define __VCS_IMPORT_DPI_STUB_get_bitstream_filename
__attribute__((weak)) SV_STRING get_bitstream_filename(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static SV_STRING (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (SV_STRING (*)(void* A_1)) dlsym(RTLD_NEXT, "get_bitstream_filename");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_bitstream_filename");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_bitstream_filename */

#ifndef __VCS_IMPORT_DPI_STUB_get_input_filename
#define __VCS_IMPORT_DPI_STUB_get_input_filename
__attribute__((weak)) SV_STRING get_input_filename(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static SV_STRING (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (SV_STRING (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_input_filename");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_input_filename");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_input_filename */

#ifndef __VCS_IMPORT_DPI_STUB_get_output_filename
#define __VCS_IMPORT_DPI_STUB_get_output_filename
__attribute__((weak)) SV_STRING get_output_filename(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static SV_STRING (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (SV_STRING (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_output_filename");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_output_filename");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_output_filename */

#ifndef __VCS_IMPORT_DPI_STUB_get_input_size
#define __VCS_IMPORT_DPI_STUB_get_input_size
__attribute__((weak)) int get_input_size(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_input_size");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_input_size");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_input_size */

#ifndef __VCS_IMPORT_DPI_STUB_get_output_size
#define __VCS_IMPORT_DPI_STUB_get_output_size
__attribute__((weak)) int get_output_size(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_output_size");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_output_size");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_output_size */

#ifndef __VCS_IMPORT_DPI_STUB_get_bs_size
#define __VCS_IMPORT_DPI_STUB_get_bs_size
__attribute__((weak)) int get_bs_size(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_bs_size");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_bs_size");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_bs_size */

#ifndef __VCS_IMPORT_DPI_STUB_get_bs_tile
#define __VCS_IMPORT_DPI_STUB_get_bs_tile
__attribute__((weak)) int get_bs_tile(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_bs_tile");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_bs_tile");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_bs_tile */

#ifndef __VCS_IMPORT_DPI_STUB_get_bs_start_addr
#define __VCS_IMPORT_DPI_STUB_get_bs_start_addr
__attribute__((weak)) int get_bs_start_addr(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_bs_start_addr");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_bs_start_addr");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_bs_start_addr */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_start_addr
#define __VCS_IMPORT_DPI_STUB_get_io_tile_start_addr
__attribute__((weak)) int get_io_tile_start_addr(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_io_tile_start_addr");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_start_addr");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_start_addr */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_map_tile
#define __VCS_IMPORT_DPI_STUB_get_io_tile_map_tile
__attribute__((weak)) int get_io_tile_map_tile(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_io_tile_map_tile");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_map_tile");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_map_tile */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_loop_dim
#define __VCS_IMPORT_DPI_STUB_get_io_tile_loop_dim
__attribute__((weak)) int get_io_tile_loop_dim(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_io_tile_loop_dim");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_loop_dim");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_loop_dim */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_extent
#define __VCS_IMPORT_DPI_STUB_get_io_tile_extent
__attribute__((weak)) int get_io_tile_extent(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2, int A_3)) dlsym(RTLD_NEXT, "get_io_tile_extent");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2, A_3);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_extent");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_extent */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_data_stride
#define __VCS_IMPORT_DPI_STUB_get_io_tile_data_stride
__attribute__((weak)) int get_io_tile_data_stride(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2, int A_3)) dlsym(RTLD_NEXT, "get_io_tile_data_stride");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2, A_3);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_data_stride");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_data_stride */

#ifndef __VCS_IMPORT_DPI_STUB_get_io_tile_cycle_stride
#define __VCS_IMPORT_DPI_STUB_get_io_tile_cycle_stride
__attribute__((weak)) int get_io_tile_cycle_stride(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2, /* INPUT */int A_3) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2, int A_3)) dlsym(RTLD_NEXT, "get_io_tile_cycle_stride");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2, A_3);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_io_tile_cycle_stride");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_io_tile_cycle_stride */

#ifndef __VCS_IMPORT_DPI_STUB_get_kernel_configuration
#define __VCS_IMPORT_DPI_STUB_get_kernel_configuration
__attribute__((weak)) void* get_kernel_configuration(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1)) dlsym(RTLD_NEXT, "get_kernel_configuration");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_kernel_configuration");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_kernel_configuration */

#ifndef __VCS_IMPORT_DPI_STUB_get_pcfg_configuration
#define __VCS_IMPORT_DPI_STUB_get_pcfg_configuration
__attribute__((weak)) void* get_pcfg_configuration(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static void* (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (void* (*)(void* A_1)) dlsym(RTLD_NEXT, "get_pcfg_configuration");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_pcfg_configuration");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_pcfg_configuration */

#ifndef __VCS_IMPORT_DPI_STUB_get_configuration_size
#define __VCS_IMPORT_DPI_STUB_get_configuration_size
__attribute__((weak)) int get_configuration_size(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_configuration_size");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_configuration_size");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_configuration_size */

#ifndef __VCS_IMPORT_DPI_STUB_get_configuration_addr
#define __VCS_IMPORT_DPI_STUB_get_configuration_addr
__attribute__((weak)) int get_configuration_addr(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_configuration_addr");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_configuration_addr");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_configuration_addr */

#ifndef __VCS_IMPORT_DPI_STUB_get_configuration_data
#define __VCS_IMPORT_DPI_STUB_get_configuration_data
__attribute__((weak)) int get_configuration_data(/* INPUT */void* A_1, /* INPUT */int A_2)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1, /* INPUT */int A_2) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1, int A_2)) dlsym(RTLD_NEXT, "get_configuration_data");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1, A_2);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_configuration_data");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_configuration_data */

#ifndef __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_addr
#define __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_addr
__attribute__((weak)) int get_pcfg_pulse_addr()
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)() = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)()) dlsym(RTLD_NEXT, "get_pcfg_pulse_addr");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_();
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_pcfg_pulse_addr");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_addr */

#ifndef __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_data
#define __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_data
__attribute__((weak)) int get_pcfg_pulse_data(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_pcfg_pulse_data");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_pcfg_pulse_data");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_pcfg_pulse_data */

#ifndef __VCS_IMPORT_DPI_STUB_get_strm_pulse_addr
#define __VCS_IMPORT_DPI_STUB_get_strm_pulse_addr
__attribute__((weak)) int get_strm_pulse_addr()
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)() = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)()) dlsym(RTLD_NEXT, "get_strm_pulse_addr");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_();
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_strm_pulse_addr");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_strm_pulse_addr */

#ifndef __VCS_IMPORT_DPI_STUB_get_strm_pulse_data
#define __VCS_IMPORT_DPI_STUB_get_strm_pulse_data
__attribute__((weak)) int get_strm_pulse_data(/* INPUT */void* A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */void* A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(void* A_1)) dlsym(RTLD_NEXT, "get_strm_pulse_data");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "get_strm_pulse_data");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_get_strm_pulse_data */

#ifndef __VCS_IMPORT_DPI_STUB_initialize_monitor
#define __VCS_IMPORT_DPI_STUB_initialize_monitor
__attribute__((weak)) int initialize_monitor(/* INPUT */int A_1)
{
    static int _vcs_dpi_stub_initialized_ = 0;
    static int (*_vcs_dpi_fp_)(/* INPUT */int A_1) = NULL;
    if (!_vcs_dpi_stub_initialized_) {
        _vcs_dpi_fp_ = (int (*)(int A_1)) dlsym(RTLD_NEXT, "initialize_monitor");
        _vcs_dpi_stub_initialized_ = 1;
    }
    if (_vcs_dpi_fp_) {
        return _vcs_dpi_fp_(A_1);
    } else {
        const char *fileName;
        int lineNumber;
        svGetCallerInfo(&fileName, &lineNumber);
        vcsMsgReport1("DPI-DIFNF", fileName, lineNumber, 0, 0, "initialize_monitor");
        return 0;
    }
}
#endif /* __VCS_IMPORT_DPI_STUB_initialize_monitor */


#ifdef __cplusplus
}
#endif

