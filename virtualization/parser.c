#include "parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ERROR 1
#define SUCCESS 0
#define GROUP_SIZE 4

// statically allocated to avoid calling
char buffer[16][BUFFER_SIZE];
static struct PlaceInfo place_values[MAX_NUM_PARSER];
static int place_info_index = 0;
static struct KernelInfo kernel_values[MAX_NUM_PARSER];
static int kernel_info_index = 0;
static struct BitstreamInfo bitstream_values[MAX_NUM_PARSER];
static int bitstream_info_index = 0;

int parse_placement_(char *filename, int *num_inputs, struct IOInfo *inputs,
                     int *num_outputs, struct IOInfo *outputs, int *num_groups,
                     int *reset) {
    FILE *fp;
    char *line = NULL;
    size_t len = 0;
    ssize_t read;
    int max_x = 0;

    *num_inputs = 0;
    *num_outputs = 0;
    // for now we assume reset is always the fist one
    // since it's set during the pre-fix IO placement
    *reset = 0;

    fp = fopen(filename, "r");
    if (fp == NULL) {
        return ERROR;
    }

    while ((read = getline(&line, &len, fp)) != -1) {
        if (read == 0) continue;
        if (line[0] == '-' || line[0] == 'B') continue;

        // we parse one char at a time
        int idx = 0, buf_index = 0;
        char c;
        int count = 0;
        do {
            c = line[idx];
            if (c == ' ' || c == '\t' || c == '\n') {
                // this is one token
                if (count > 0) {
                    buffer[buf_index][count] = '\0';
                    buf_index++;
                    count = 0;
                }
            } else {
                buffer[buf_index][count] = c;
                count++;
            }
            idx++;
        } while (c != EOF && c != '\n' && idx < read);
        if (buf_index < 4) continue;
        char *s_x = buffer[1];
        char *s_y = buffer[2];
        int x = atoi(s_x);// NOLINT
        int y = atoi(s_y);// NOLINT

        if (x > max_x) max_x = x;

        char *id = buffer[3];
        char *name = buffer[0];
        if (id[1] == 'I') {
            // this is a data port
            if (strstr(name, "out") != NULL) {
                // it's output
                outputs[*num_outputs].io = Output;
                outputs[*num_outputs].pos.x = x;
                outputs[*num_outputs].pos.y = y;
                *num_outputs = *num_outputs + 1;
            } else {
                // it's input
                inputs[*num_inputs].io = Input;
                inputs[*num_inputs].pos.x = x;
                inputs[*num_inputs].pos.y = y;
                *num_inputs = *num_inputs + 1;
            }
        }
    }

    *num_groups = 0;
    while (max_x > 0) {
        *num_groups = *num_groups + 1;
        max_x -= GROUP_SIZE;
    }


    // clean up
    fclose(fp);
    if (line) free(line);
    return SUCCESS;
}

void *parse_placement(char *filename) {
    // TODO: use arena-based allocator?
    if (place_info_index >= MAX_NUM_PARSER) return NULL;
    struct PlaceInfo *place_info = &place_values[place_info_index++];

    parse_placement_(filename, &place_info->num_inputs, place_info->inputs, &place_info->num_outputs,
                     place_info->outputs, &place_info->num_groups, &place_info->reset_port);

    return place_info;
}

void *parse_bitstream(char *filename) {
    if (bitstream_info_index >= MAX_NUM_PARSER) return NULL;

    int num_bs = 0;
    struct BitstreamInfo *bs_info = &bitstream_values[bitstream_info_index++];
    FILE *fp;
    if (filename[0] != '\0') {
        fp = fopen(filename, "r");
        if (fp == NULL) {
            printf("Could not open file %s", filename);
            return 0;
        }
        for (char c = getc(fp); c != EOF; c = getc(fp)) {
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

void *parse_metadata(char *filename) {
    if (kernel_info_index >= MAX_NUM_PARSER) return NULL;
    struct KernelInfo *info = &kernel_values[kernel_info_index++];

    FILE *fp;
    char *line = NULL;
    size_t len = 0;
    ssize_t read;

    fp = fopen(filename, "r");
    if (fp == NULL) {
        return NULL;
    }

    char *dir;
    dir = get_prefix(filename, '/');

    int num_inputs = 0;
    int num_outputs = 0;

    while ((read = getline(&line, &len, fp)) != -1) {
        int idx = 0, buf_index = 0;
        char c;
        int count = 0;
        do {
            c = line[idx];
            if (c == '=' || c == '\n') {
                buffer[buf_index][count] = '\0';
                buf_index++;
                count = 0;
            } else {
                buffer[buf_index][count] = c;
                count++;
            }

            idx++;
        } while (c != '\n' && c != EOF && idx < read);
        if (buf_index != 2)
            return NULL;

        // decode the information
        if (strncmp(buffer[0], "placement", strlen("placement")) == 0) {
            // this is placement file
            strncpy(info->placement_filename, dir,
                    strnlen(dir, BUFFER_SIZE));
            strncat(info->placement_filename, buffer[1],
                    strnlen(buffer[1], BUFFER_SIZE));
        } else if (strncmp(buffer[0], "bitstream", strlen("bitstream")) == 0) {
            strncpy(info->bitstream_filename, dir,
                    strnlen(dir, BUFFER_SIZE));
            strncat(info->bitstream_filename, buffer[1],
                    strnlen(buffer[1], BUFFER_SIZE));
        } else if (strncmp(buffer[0], "input", strlen("input")) == 0) {
            strncpy(info->input_filenames[num_inputs], dir,
                    strnlen(dir, BUFFER_SIZE));
            strncat(info->input_filenames[num_inputs++], buffer[1],
                    strnlen(buffer[1], BUFFER_SIZE));
        } else if (strncmp(buffer[0], "output", strlen("output")) == 0) {
            strncpy(info->output_filenames[num_outputs], dir,
                    strnlen(dir, BUFFER_SIZE));
            strncat(info->output_filenames[num_outputs++], buffer[1],
                    strnlen(buffer[1], BUFFER_SIZE));
        }
    }

    // free up
    fclose(fp);
    if (line) free(line);

    info->place_info = parse_placement(info->placement_filename);
    info->bitstream_info = parse_bitstream(info->bitstream_filename);

    // compute the input size
    for (int i = 0; i < num_inputs; i++) {
        if (info->input_filenames[i][0] != '\0') {
            fp = fopen(info->input_filenames[i], "r");
            if (fp) {
                fseek(fp, 0L, SEEK_END);
                info->place_info->input_size[i] = (int) ftell(fp);
                fclose(fp);
            }
        }
    }

    // compute the output size
    for (int i = 0; i < num_outputs; i++) {
        if (info->output_filenames[i][0] != '\0') {
            fp = fopen(info->output_filenames[i], "r");
            if (fp) {
                fseek(fp, 0L, SEEK_END);
                info->place_info->output_size[i] = (int) ftell(fp);
                fclose(fp);
            }
        }
    }

    return info;
}

void *get_place_info(void *info) {
    GET_KERNEL_INFO(info);
    return kernel_info->place_info;
}

void *get_bs_info(void *info) {
    GET_KERNEL_INFO(info);
    return kernel_info->bitstream_info;
}

void *get_input_info(void *info, int index) {
    GET_PLACE_INFO(info);
    return &place_info->inputs[index];
}

void *get_output_info(void *info, int index) {
    GET_PLACE_INFO(info);
    return &place_info->outputs[index];
}

int get_num_groups(void *info) {
    GET_PLACE_INFO(info);
    return place_info->num_groups;
}

int get_group_start(void *info) {
    GET_PLACE_INFO(info);
    return place_info->group_start;
}

int get_num_inputs(void *info) {
    GET_PLACE_INFO(info);
    return place_info->num_inputs;
}

int get_num_outputs(void *info) {
    GET_PLACE_INFO(info);
    return place_info->num_outputs;
}

int get_input_x(void *info, int index) {
    GET_PLACE_INFO(info);
    if (index >= place_info->num_inputs) {
        return -1;
    } else {
        return place_info->inputs[index].pos.x;
    }
}

int get_input_y(void *info, int index) {
    GET_PLACE_INFO(info);
    if (index >= place_info->num_inputs) {
        return -1;
    } else {
        return place_info->inputs[index].pos.y;
    }
}

int get_output_x(void *info, int index) {
    GET_PLACE_INFO(info);
    if (index >= place_info->num_outputs) {
        return -1;
    } else {
        return place_info->outputs[index].pos.x;
    }
}

int get_output_y(void *info, int index) {
    GET_PLACE_INFO(info);
    if (index >= place_info->num_outputs) {
        return -1;
    } else {
        return place_info->outputs[index].pos.y;
    }
}

int get_reset_index(void *info) {
    GET_PLACE_INFO(info);
    return place_info->reset_port;
}

char *get_placement_filename(void *info) {
    GET_KERNEL_INFO(info);
    return kernel_info->placement_filename;
}

char *get_bitstream_filename(void *info) {
    GET_KERNEL_INFO(info);
    return kernel_info->bitstream_filename;
}

char *get_input_filename(void *info, int index) {
    GET_KERNEL_INFO(info);
    return kernel_info->input_filenames[index];
}

char *get_output_filename(void *info, int index) {
    GET_KERNEL_INFO(info);
    return kernel_info->output_filenames[index];
}

int get_input_size(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->input_size[index];
}

int get_input_start_addr(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->inputs[index].start_addr;
}

int get_input_tile(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->inputs[index].tile;
}

int get_output_size(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->output_size[index];
}

int get_output_start_addr(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->outputs[index].start_addr;
}

int get_output_tile(void *info, int index) {
    GET_PLACE_INFO(info);
    return place_info->outputs[index].tile;
}

int get_bs_start_addr(void *info) {
    GET_BS_INFO(info);
    return bs_info->start_addr;
}

int get_bs_size(void *info) {
    GET_BS_INFO(info);
    return bs_info->size;
}

int get_bs_tile(void *info) {
    GET_BS_INFO(info);
    return bs_info->tile;
}

char *get_prefix(const char *s, char t)
{
    const char * last = strrchr(s, t);
    if(last != NULL) {
        const size_t len = (size_t) (last - s);
        char * const n = malloc(len + 2);
        memcpy(n, s, len);
        n[len] = '/';
        n[len+1] = '\0';
        return n;
    }
    return NULL;
}
