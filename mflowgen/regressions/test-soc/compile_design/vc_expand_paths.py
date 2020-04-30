#!/usr/bin/env python

###############################################################################
# Description:
#
# This script expands file and directory paths within a VCS file list
###############################################################################
import os
import argparse
import re

def vc_expand_path(path, base_dir, file_name, line_no):
    expanded_vars = os.path.expandvars(path);
    unresolved = re.findall('\$\{(\w+)\}', expanded_vars)
    if unresolved:
        msg = '[{}:{}]'.format(file_name, line_no)
        msg = msg + ' unresolved environment variables: {}'.format(unresolved)
        raise ValueError(msg)
    norm_path = os.path.abspath(os.path.normpath(os.path.join(base_dir, expanded_vars)))
    if not os.path.exists(norm_path):
        raise FileNotFoundError('[{}:{}] expanded path {} does not exist'.format(file_name, line_no, norm_path))
    return norm_path

def vc_expand_paths(input_file, output_file):
    # make sure input file exists
    if not os.path.isfile(input_file):
        raise FileNotFoundError('file ' + input_file + ' not found')

    with open(input_file, 'r') as in_fh:
        base_dir = os.path.dirname(input_file)
        with open(output_file, 'w') as out_fh:
            line = in_fh.readline()
            line_no = 1
            while (line != ''):
                l = line.strip()
                # simply write back lines of no interest
                if not (l.startswith('-v') or l.startswith('-y') or l.startswith('+incdir+')):
                    out_fh.write('{}\n'.format(l))
                else:
                    # get leading qualifier
                    qualifier = re.search('^(-y|-v|\+incdir\+)', l).group(1)
                    # get specified file/directory path
                    if(qualifier == '+incdir+'):
                        path = re.search('^\+incdir\+(.*)', l).group(1)
                    else:
                        path = re.search('^(-y|-v) *(.*)', l).group(2)
                    # if no directory listed, error
                    # otherwise, process directory
                    if (path == ''):
                        raise ValueError('[{}:{}] no directory listed'.format(input_file, line_no))
                    else:
                        expanded_path = vc_expand_path(path, base_dir, input_file, line_no)
                        if(qualifier == '+incdir+'):
                            out_fh.write('{}{}\n'.format(qualifier, expanded_path))
                        else:
                            out_fh.write('{} {}\n'.format(qualifier, expanded_path))

                # next line
                line = in_fh.readline()
                line_no = line_no + 1

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(description='Expand paths in a VCS file list')
    parser.add_argument('input_file', type=str, help='Path to input file')
    parser.add_argument('output_file', type=str, help='Path to output file')
    args = parser.parse_args()

    vc_expand_paths(args.input_file, args.output_file)
