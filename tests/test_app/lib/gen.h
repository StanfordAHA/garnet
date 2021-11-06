#ifndef CONFIG_GEN_LIBRARY_H
#define CONFIG_GEN_LIBRARY_H

void *get_kernel_configuration(void *info);
void *get_pcfg_configuration(void *info);
int get_configuration_size(void *info);
int get_configuration_addr(void *info, int index);
int get_configuration_data(void *info, int index);

int get_pcfg_pulse_addr();
int get_pcfg_pulse_data(void *info);
int get_strm_pulse_addr();
int get_strm_pulse_data(void *info);

#endif
