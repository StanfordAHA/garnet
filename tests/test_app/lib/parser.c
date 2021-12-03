#include "parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define ERROR 1
#define SUCCESS 0
#define GROUP_SIZE 4

#define GET_IO_INFO(info) struct IOInfo *io_info = \
                              (struct IOInfo *)info

#define GET_IO_TILE_INFO(info) struct IOTileInfo *io_info = \
                                   (struct IOTileInfo *)info

// statically allocated to avoid calling
static struct KernelInfo kernel_info_list[MAX_NUM_KERNEL];
static int kernel_info_index = 0;
static struct BitstreamInfo bitstream_info_list[MAX_NUM_KERNEL];
static int bitstream_info_index = 0;
static struct IOInfo io_info_list[MAX_NUM_KERNEL * MAX_NUM_IO];
static int io_info_index = 0;

// parse the place file to calculate the number of columns used
int parse_num_group(struct KernelInfo *info)
{

    char *filename = info->placement_filename;

    FILE *fp;
    char *line = NULL;
    size_t len = 0;
    size_t read;
    int max_x = 0;
    char buffer[8][BUFFER_SIZE];

    fp = fopen(filename, "r");
    if (fp == NULL)
    {
        printf("Could not open file %s\n", filename);
        return ERROR;
    }

    while ((read = getline(&line, &len, fp)) != -1)
    {
        if (read == 0)
            continue;
        if (line[0] == '-' || line[0] == 'B')
            continue;

        // we parse one char at a time
        int idx = 0, buf_index = 0;
        char c;
        int count = 0;
        do
        {
            c = line[idx];
            if (c == ' ' || c == '\t' || c == '\n')
            {
                // this is one token
                if (count > 0)
                {
                    buffer[buf_index][count] = '\0';
                    buf_index++;
                    count = 0;
                }
            }
            else
            {
                buffer[buf_index][count] = c;
                count++;
            }
            idx++;
        } while (c != EOF && c != '\n' && idx < read);
        if (buf_index < 4)
            continue;
        char *s_x = buffer[1];
        // char *s_y = buffer[2];
        int x = atoi(s_x); // NOLINT
        // int y = atoi(s_y); // NOLINT

        if (x > max_x)
            max_x = x;
    }

    info->num_groups = (max_x + GROUP_SIZE - 1) / GROUP_SIZE;

    // clean up
    fclose(fp);
    if (line)
        free(line);
    return SUCCESS;
}

int parse_io_tile_info(struct IOTileInfo *io_tile_info, json_t const *io_tile_json)
{
    int cnt;

    // parse x position
    json_t const *x_pos_json = json_getProperty(io_tile_json, "x_pos");
    if (!x_pos_json || JSON_INTEGER != json_getType(x_pos_json))
    {
        puts("Error, the x_pos property is not found.");
        exit(1);
    }
    io_tile_info->pos.x = json_getInteger(x_pos_json);

    // parse y position
    json_t const *y_pos_json = json_getProperty(io_tile_json, "y_pos");
    if (!y_pos_json || JSON_INTEGER != json_getType(y_pos_json))
    {
        puts("Error, the y_pos property is not found.");
        exit(1);
    }
    io_tile_info->pos.y = json_getInteger(y_pos_json);

    // parse addr
    json_t const *addr_json = json_getProperty(io_tile_json, "addr");
    if (!addr_json || JSON_OBJ != json_getType(addr_json))
    {
        puts("Error, the addr property is not found.");
        exit(1);
    }

    // parse dimensionality
    json_t const *dim_json = json_getProperty(addr_json, "dimensionality");
    if (!dim_json || JSON_INTEGER != json_getType(dim_json))
    {
        puts("Error, the dim property is not found.");
        exit(1);
    }
    io_tile_info->loop_dim = json_getInteger(dim_json);

    // parse cycle_start_addr
    json_t const *cycle_start_addr_list_json = json_getProperty(addr_json, "cycle_starting_addr");
    if (!cycle_start_addr_list_json || JSON_ARRAY != json_getType(cycle_start_addr_list_json))
    {
        puts("Error, the cycle_starting_addr_list property is not found.");
        exit(1);
    }
    // cycle_start_addr_json type is list, but we only need the first one
    json_t const *cycle_start_addr_json;
    cycle_start_addr_json = json_getChild(cycle_start_addr_list_json);
    io_tile_info->cycle_start_addr = json_getInteger(cycle_start_addr_json);

    // parse cycle stride
    json_t const *cycle_stride_list_json = json_getProperty(addr_json, "cycle_stride");
    if (!cycle_stride_list_json || JSON_ARRAY != json_getType(cycle_stride_list_json))
    {
        puts("Error, the cycle_stride_list property is not found.");
        exit(1);
    }

    cnt = 0;
    json_t const *stride_json;
    for (stride_json = json_getChild(cycle_stride_list_json); stride_json != 0; stride_json = json_getSibling(stride_json))
    {
        io_tile_info->cycle_stride[cnt] = json_getInteger(stride_json);
        cnt++;
    }

    // parse start_addr
    json_t const *start_addr_list_json;
    if (io_tile_info->io == Input)
    {
        start_addr_list_json = json_getProperty(addr_json, "read_data_starting_addr");
    }
    else
    {
        start_addr_list_json = json_getProperty(addr_json, "write_data_starting_addr");
    }
    if (!start_addr_list_json || JSON_ARRAY != json_getType(start_addr_list_json))
    {
        puts("Error, the data_starting_addr_list property is not found.");
        exit(1);
    }
    // start_addr_json type is list, but we only need the first one
    json_t const *start_addr_json;
    start_addr_json = json_getChild(start_addr_list_json);
    io_tile_info->start_addr = json_getInteger(start_addr_json);

    // parse data stride
    json_t const *data_stride_list_json;
    if (io_tile_info->io == Input)
    {
        data_stride_list_json = json_getProperty(addr_json, "read_data_stride");
    }
    else
    {
        data_stride_list_json = json_getProperty(addr_json, "write_data_stride");
    }
    if (!data_stride_list_json || JSON_ARRAY != json_getType(data_stride_list_json))
    {
        puts("Error, the data_stride_list property is not found.");
        exit(1);
    }

    cnt = 0;
    json_t const *data_stride_json;
    for (data_stride_json = json_getChild(data_stride_list_json); data_stride_json != 0; data_stride_json = json_getSibling(data_stride_json))
    {
        io_tile_info->data_stride[cnt] = json_getInteger(data_stride_json);
        cnt++;
    }

    // parse extent
    json_t const *extent_list_json = json_getProperty(addr_json, "extent");
    if (!extent_list_json || JSON_ARRAY != json_getType(extent_list_json))
    {
        puts("Error, the extent_list property is not found.");
        exit(1);
    }

    cnt = 0;
    json_t const *extent_json;
    for (extent_json = json_getChild(extent_list_json); extent_json != 0; extent_json = json_getSibling(extent_json))
    {
        io_tile_info->extent[cnt] = json_getInteger(extent_json);
        cnt++;
    }

    return SUCCESS;
}

void *parse_io(json_t const *io_json, enum IO io)
{
    if (io_info_index >= MAX_NUM_KERNEL * MAX_NUM_IO)
        return NULL;
    struct IOInfo *io_info = &io_info_list[io_info_index++];

    io_info->io = io;

    json_t const *shape_json = json_getProperty(io_json, "shape");
    if (!shape_json || JSON_ARRAY != json_getType(shape_json))
    {
        puts("Error, the shape property is not found.");
        exit(1);
    }

    int channel[8] = {0};
    int cnt = 0;
    json_t const *channel_json;
    for (channel_json = json_getChild(shape_json);
         channel_json != 0; channel_json = json_getSibling(channel_json))
    {
        channel[cnt] = json_getInteger(channel_json);
        cnt++;
    }

    // parse io_tile list
    json_t const *io_tile_list_json = json_getProperty(io_json, "io_tiles");
    if (!io_tile_list_json || JSON_ARRAY != json_getType(io_tile_list_json))
    {
        puts("Error, the io_tiles property is not found.");
        exit(1);
    }

    // parse each io_tile
    cnt = 0;
    json_t const *io_tile_json;
    for (io_tile_json = json_getChild(io_tile_list_json);
         io_tile_json != 0; io_tile_json = json_getSibling(io_tile_json))
    {
        if (JSON_OBJ == json_getType(io_tile_json))
        {
            io_info->io_tiles[cnt].io = io;
            parse_io_tile_info(&io_info->io_tiles[cnt], io_tile_json);
            cnt++;
        }
    }
    io_info->num_io_tiles = cnt;

    // If the number of io_tiles is larger than 1, then the number of io_tiles
    // should be equal to the innermost_channel
    if (io_info->num_io_tiles > 1)
    {
        assert(io_info->num_io_tiles == channel[0]);
    }

    return io_info;
}

void *parse_bitstream(char *filename)
{
    if (bitstream_info_index >= MAX_NUM_KERNEL)
        return NULL;
    struct BitstreamInfo *bs_info = &bitstream_info_list[bitstream_info_index++];
    FILE *fp;

    int num_bs = 0;

    // count the number of lines in bitstream file and store it to bs_info->size
    if (filename[0] != '\0')
    {
        fp = fopen(filename, "r");
        if (fp == NULL)
        {
            printf("Could not open file %s", filename);
            return 0;
        }
        for (char c = getc(fp); c != EOF; c = getc(fp))
        {
            if (c == '\n') // Increment count if this character is newline
                num_bs++;
        }
        fclose(fp);
    }
    // add 1 because the last line does not have new line
    num_bs++;
    bs_info->size = num_bs;

    return bs_info;
}

void *parse_metadata(char *filename)
{
    if (kernel_info_index >= MAX_NUM_KERNEL)
        return NULL;
    struct KernelInfo *info = &kernel_info_list[kernel_info_index++];

    FILE *fp;
    char *json_buffer = NULL;
    long l_size;
    int cnt;

    fp = fopen(filename, "rb");
    if (fp == NULL)
    {
        return NULL;
    }

    // get current directory
    char *dir;
    // Need to free directory
    dir = get_prefix(filename, '/');

    // calculate metadata file size and save it to l_size
    fseek(fp, 0L, SEEK_END);
    l_size = ftell(fp);
    rewind(fp);

    // allocate memory for entire content
    json_buffer = malloc(l_size + 1);
    if (!json_buffer)
    {
        fclose(fp);
        fputs("memory allocation fails", stderr);
        exit(1);
    }

    // copy the file into the buffer
    if (fread(json_buffer, l_size, 1, fp) != 1)
    {
        fclose(fp);
        fputs("json file read fails", stderr);
        exit(1);
    }

    // parse json file
    json_t pool[MAX_JSON_FIELDS];
    json_t const *json = json_create(json_buffer, pool, MAX_JSON_FIELDS);
    if (!json)
    {
        fputs("Error json create", stderr);
        exit(1);
    }

    // Parse testing field
    json_t const *testing_json = json_getProperty(json, "testing");
    if (!testing_json || JSON_OBJ != json_getType(testing_json))
    {
        puts("Error, the testing property is not found.");
        exit(1);
    }

    // parse coreir field
    json_t const *coreir_json = json_getProperty(testing_json, "coreir");
    if (!coreir_json || JSON_TEXT != json_getType(coreir_json))
    {
        puts("Error, the coreir property is not found.");
        exit(1);
    }
    strncpy(info->coreir_filename, dir, strnlen(dir, BUFFER_SIZE));
    strncat(info->coreir_filename, json_getValue(coreir_json), BUFFER_SIZE);

    // parse bistream field
    json_t const *bs_json = json_getProperty(testing_json, "bitstream");
    if (!bs_json || JSON_TEXT != json_getType(bs_json))
    {
        puts("Error, the bitstream property is not found.");
        exit(1);
    }
    strncpy(info->bitstream_filename, dir, strnlen(dir, BUFFER_SIZE));
    strncat(info->bitstream_filename, json_getValue(bs_json), BUFFER_SIZE);

    // parse placement field
    json_t const *place_json = json_getProperty(testing_json, "placement");
    if (!place_json || JSON_TEXT != json_getType(place_json))
    {
        puts("Error, the placement property is not found.");
        exit(1);
    }
    strncpy(info->placement_filename, dir, strnlen(dir, BUFFER_SIZE));
    strncat(info->placement_filename, json_getValue(place_json), BUFFER_SIZE);

    // store bitstream to bitstream_info

    // TODO: bitstream Config info should be stored elsewhere
    // the size of bitstream will be saved in bitstrea_info
    info->bitstream_info = parse_bitstream(info->bitstream_filename);

    // Parse IO scheduling information
    json_t const *IOs_json = json_getProperty(json, "IOs");

    // parse inputs
    json_t const *input_list_json = json_getProperty(IOs_json, "inputs");
    if (!input_list_json || JSON_ARRAY != json_getType(input_list_json))
    {
        puts("Error, the input list property is not found.");
        exit(1);
    }

    json_t const *input_json;
    for (input_json = json_getChild(input_list_json), cnt = 0;
         input_json != 0; input_json = json_getSibling(input_json), cnt++)
    {
        if (JSON_OBJ == json_getType(input_json))
        {
            info->input_info[cnt] = parse_io(input_json, Input);
            strncpy(info->input_info[cnt]->filename, dir, strnlen(dir, BUFFER_SIZE));
            strncat(info->input_info[cnt]->filename, json_getPropertyValue(input_json, "datafile"), BUFFER_SIZE);
        }
    }
    info->num_inputs = cnt;

    // parse outputs
    json_t const *output_list_json = json_getProperty(IOs_json, "outputs");
    if (!output_list_json || JSON_ARRAY != json_getType(output_list_json))
    {
        puts("Error, the output list property is not found.");
        exit(1);
    }

    json_t const *output_json;
    for (output_json = json_getChild(output_list_json), cnt = 0;
         output_json != 0; output_json = json_getSibling(output_json), cnt++)
    {
        if (JSON_OBJ == json_getType(output_json))
        {
            info->output_info[cnt] = parse_io(output_json, Output);
            strncpy(info->output_info[cnt]->filename, dir, strnlen(dir, BUFFER_SIZE));
            strncat(info->output_info[cnt]->filename, json_getPropertyValue(output_json, "datafile"), BUFFER_SIZE);
        }
    }
    info->num_outputs = cnt;

    // parse interleaved_input field
    json_t const *input_data_list_json = json_getProperty(testing_json, "interleaved_input");
    if (!input_data_list_json || JSON_ARRAY != json_getType(input_data_list_json))
    {
        puts("Error, the interleaved_input property is not found.");
        exit(1);
    }

    // Parse file byte size by reading pgm image file
    // TODO: Make this as a function
    FILE *fp2;
    for (int i = 0; i < info->num_inputs; i++)
    {
        if (*info->input_info[i]->filename != '\0')
        {
            fp2 = fopen(info->input_info[i]->filename, "r");
            if (fp2)
            {
                int name_len = strlen(info->input_info[i]->filename);
                if (strncmp(&info->input_info[i]->filename[name_len - 3], "raw", strlen("raw")) == 0)
                {
                    fseek(fp2, 0L, SEEK_END);
                    info->input_info[i]->filesize = (int)ftell(fp2);
                }
                else if (strncmp(&info->input_info[i]->filename[name_len - 3], "hex", strlen("hex")) == 0)
                {
                    fseek(fp2, 0L, SEEK_END);
                    info->input_info[i]->filesize = 2 * (((int)ftell(fp2)) / 5);
                }
                else
                {
                    char c;
                    int ch1, ch2, bitwidth, filesize;
                    // skip the first line
                    while (true)
                    {
                        c = fgetc(fp2);
                        if (c == '\n')
                            break;
                    }
                    fscanf(fp2, "%d %d\n%d", &ch1, &ch2, &bitwidth);
                    if (bitwidth == 65535)
                    {
                        filesize = ch1 * ch2 * 2;
                    }
                    else
                    {
                        filesize = ch1 * ch2;
                    }
                    info->input_info[i]->filesize = filesize;
                }
                fclose(fp2);
                printf("Input %0d: %s - %0d Byte.\n", i, info->input_info[i]->filename, info->input_info[i]->filesize);
            }
            else
            {
                printf("Error, input file %s does not exist.\n", info->input_info[i]->filename);
                exit(1);
            }
        }
    }

    // TODO: Make this as a function
    for (int i = 0; i < info->num_outputs; i++)
    {
        if (*info->output_info[i]->filename != '\0')
        {
            fp2 = fopen(info->output_info[i]->filename, "r");
            if (fp2)
            {
                int name_len = strlen(info->output_info[i]->filename);
                if (strncmp(&info->output_info[i]->filename[name_len - 3], "raw", strlen("raw")) == 0)
                {
                    fseek(fp2, 0L, SEEK_END);
                    info->output_info[i]->filesize = (int)ftell(fp2);
                }
                else if (strncmp(&info->output_info[i]->filename[name_len - 3], "hex", strlen("hex")) == 0)
                {
                    fseek(fp2, 0L, SEEK_END);
                    // When in hex format, every character (including whitespace) is considered as one data
                    info->output_info[i]->filesize = 2 * (((int)ftell(fp2)) / 5);
                }
                else
                {
                    char c;
                    int ch1, ch2, bitwidth, filesize;
                    // skip the first line
                    while (true)
                    {
                        c = fgetc(fp2);
                        if (c == '\n')
                            break;
                    }
                    fscanf(fp2, "%d %d\n%d", &ch1, &ch2, &bitwidth);
                    if (bitwidth == 65535)
                    {
                        filesize = ch1 * ch2 * 2;
                    }
                    else
                    {
                        filesize = ch1 * ch2;
                    }
                    info->output_info[i]->filesize = filesize;
                }
                fclose(fp2);
                printf("Output %0d: %s - %0d Byte.\n", i, info->output_info[i]->filename, info->output_info[i]->filesize);
            }
            else
            {
                printf("Error, output file %s does not exist.\n", info->output_info[i]->filename);
                exit(1);
            }
        }
    }

    // parse number of groups
    // TODO: make a better way to calculate number of groups used
    // update scheduling group size by parsing place file
    parse_num_group(info);

    // set reset_port
    // for now we assume soft reset is always placed to the fist column by pnr
    info->reset_port = 0;

    // free up the buffer and close fp
    fclose(fp);
    free(dir);
    free(json_buffer);

    return info;
}

void *get_bs_info(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->bitstream_info;
}

void *get_input_info(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->input_info[index];
}

void *get_output_info(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->output_info[index];
}

int get_num_groups(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->num_groups;
}

int get_group_start(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->group_start;
}

int get_num_inputs(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->num_inputs;
}

int get_num_outputs(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->num_outputs;
}

void *get_io_tile_info(void *info, int index)
{
    GET_IO_INFO(info);
    return &io_info->io_tiles[index];
}

int get_num_io_tiles(void *info, int index)
{
    GET_IO_INFO(info);
    return io_info->num_io_tiles;
}

int get_io_tile_x(void *info, int index)
{
    GET_IO_INFO(info);
    if (index >= io_info->num_io_tiles)
    {
        return -1;
    }
    else
    {
        return io_info->io_tiles[index].pos.x;
    }
}

int get_io_tile_y(void *info, int index)
{
    GET_IO_INFO(info);
    if (index >= io_info->num_io_tiles)
    {
        return -1;
    }
    else
    {
        return io_info->io_tiles[index].pos.y;
    }
}

int get_reset_index(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->reset_port;
}

char *get_placement_filename(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->placement_filename;
}

char *get_bitstream_filename(void *info)
{
    GET_KERNEL_INFO(info);
    return kernel_info->bitstream_filename;
}

char *get_input_filename(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->input_info[index]->filename;
}

char *get_output_filename(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->output_info[index]->filename;
}

int get_input_size(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->input_info[index]->filesize;
}

int get_io_tile_start_addr(void *info, int index)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].start_addr;
}

int get_io_tile_cycle_start_addr(void *info, int index)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].cycle_start_addr;
}

int get_io_tile_map_tile(void *info, int index)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].tile;
}

int get_io_tile_loop_dim(void *info, int index)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].loop_dim;
}

int get_io_tile_data_stride(void *info, int index, int stride_idx)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].data_stride[stride_idx];
}

int get_io_tile_cycle_stride(void *info, int index, int stride_idx)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].cycle_stride[stride_idx];
}

int get_io_tile_extent(void *info, int index, int extent_idx)
{
    GET_IO_INFO(info);
    return io_info->io_tiles[index].extent[extent_idx];
}

int get_output_size(void *info, int index)
{
    GET_KERNEL_INFO(info);
    return kernel_info->output_info[index]->filesize;
}

int get_bs_start_addr(void *info)
{
    GET_BS_INFO(info);
    return bs_info->start_addr;
}

int get_bs_size(void *info)
{
    GET_BS_INFO(info);
    return bs_info->size;
}

int get_bs_tile(void *info)
{
    GET_BS_INFO(info);
    return bs_info->tile;
}

char *get_prefix(const char *s, char t)
{
    // store the last word after 't' to last (including 't')
    const char *last = strrchr(s, t);
    if (last != NULL)
    {
        const size_t len = (size_t)(last - s);
        char *const n = malloc(len + 2);
        memcpy(n, s, len);
        n[len] = '/';
        n[len + 1] = '\0';
        return n;
    }
    else
    {
        char *const n = malloc(3);
        strcpy(n, "./\0");
        return n;
    }
}
