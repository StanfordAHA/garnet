#ifndef VIRTUALIZE_META_LIBRARY_H
#define VIRTUALIZE_META_LIBRARY_H

#define MAX_NUM_IO 32
#define BUFFER_SIZE 1024
#define MAX_NUM_PARSER 16
#define GET_PLACE_INFO(info) struct PlaceInfo *place_info = \
                                    (struct PlaceInfo *) info

#define GET_KERNEL_INFO(info) struct KernelInfo *kernel_info = \
                                    (struct KernelInfo *) info

#define GET_CONFIG_INFO(info) struct ConfigInfo *config_info = \
                                    (struct ConfigInfo *) info

#define GET_BS_INFO(info) struct BitstreamInfo *bs_info = \
                                    (struct BitstreamInfo *) info

#define GET_IO_INFO(info) struct IOInfo *io_info = \
                                    (struct IOInfo *) info

#define MAX_CONFIG 20

struct Configuration {
    int addr;
    int data;
};

struct ConfigInfo {
    int num_config;
    struct Configuration config[MAX_CONFIG];
};

struct Position {
    int x;
    int y;
};
enum IO {Input = 0, Output = 1}; 
struct IOInfo {
    struct Position pos; 
    enum IO io;

    int tile;
    int size; 
    int start_addr;

    struct ConfigInfo config;
};

struct BitstreamInfo {
    int tile;
    int size;
    int start_addr;

    struct ConfigInfo config;
};

struct PlaceInfo {
    int num_groups;
    int num_inputs;
    int num_outputs;
    int group_start;

    struct IOInfo inputs[MAX_NUM_IO];
    struct IOInfo outputs[MAX_NUM_IO];

    struct ConfigInfo config;

    int input_size[MAX_NUM_IO];
    int output_size[MAX_NUM_IO];

    // index to the inputs, need to multiply by 2
    int reset_port;
};

struct KernelInfo {
    char placement_filename[BUFFER_SIZE];
    char bitstream_filename[BUFFER_SIZE];

    char input_filenames[MAX_NUM_IO][BUFFER_SIZE];
    char output_filenames[MAX_NUM_IO][BUFFER_SIZE];

    struct PlaceInfo *place_info;
    struct BitstreamInfo *bitstream_info;
};

void *parse_placement(char *filename);
void *parse_metadata(char *filename);
void *get_place_info(void *info);
void *get_bs_info(void *info);
void *get_input_info(void *info, int index);
void *get_output_info(void *info, int index);

// helper functions to access data from SV
int get_num_groups(void *info);
int get_group_start(void *info);
int get_num_inputs(void *info);
int get_num_outputs(void *info);
int get_input_x(void *info, int index);
int get_input_y(void *info, int index);
int get_output_x(void *info, int index);
int get_output_y(void *info, int index);
int get_reset_index(void *info);

char *get_placement_filename(void *info);
char *get_bitstream_filename(void *info);
char *get_input_filename(void *info, int index);
char *get_output_filename(void *info, int index);
int get_input_size(void *info, int index);
int get_output_size(void *info, int index);

int get_input_start_addr(void *info, int index);
int get_input_size(void *info, int index);
int get_input_tile(void *info, int index);
int get_output_start_addr(void *info, int index);
int get_output_size(void *info, int index);
int get_output_tile(void *info, int index);

int get_bs_start_addr(void *info);
int get_bs_size(void *info);
int get_bs_tile(void *info);
char *get_prefix(const char *s, char t);

#endif//VIRTUALIZE_META_LIBRARY_H
