#!/bin/bash

awk '{if($2=="No" && $3=="module") {print $7}}' v2lvs.log > missing_module_list.txt
