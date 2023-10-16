# remember current path
root_path=$(pwd)

# create a dedicated folder for v2sp
work_dir=v2sp
if [ -d ${work_dir} ]; then
    rm -rf ${work_dir}/*
else
    mkdir ${work_dir}
fi

# concatenate .v and .sp files
if [ -f inputs/*.sp ]; then
    cat inputs/adk/*.sp inputs/*.sp > ${work_dir}/cells.sp
else
    cat inputs/adk/*.sp > ${work_dir}/cells.sp
fi
cat inputs/*.lvs.v > ${work_dir}/design.lvs.v

# convert design.lvs.v to design.lvs.sp
cd ${work_dir}
v2lvs \
    -i \
    -lsp cells.sp \
    -s cells.sp \
    -v design.lvs.v \
    -o design.lvs.sp

# return to the original path
cd ${root_path}
