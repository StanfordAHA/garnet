import os

# remember current path
root_path = os.getcwd()

# create a dedicated folder for v2sp
work_dir = 'v2sp'
if os.path.isdir(work_dir):
    os.system(f'rm -rf {work_dir}/*')
else:
    os.mkdir(work_dir)

# concatenate .v and .sp files
sp_files = []
for sp_filename in os.listdir('inputs/adk'):
    if sp_filename.endswith('.sp') or sp_filename.endswith('.spi'):
        sp_files.append(os.path.join('inputs/adk', sp_filename))

for sp_filename in os.listdir('inputs'):
    if sp_filename.endswith('.sp') or sp_filename.endswith('.spi'):
        sp_files.append(os.path.join('inputs', sp_filename))

with open(os.path.join(work_dir, 'cells.sp'), 'w') as sp_file:
    for sp_filename in sp_files:
        with open(sp_filename, 'r') as f:
            sp_file.write(f.read())

with open(os.path.join(work_dir, 'design.lvs.v'), 'w') as v_file:
    for v_filename in os.listdir('inputs'):
        if v_filename.endswith('.lvs.v'):
            with open(os.path.join('inputs', v_filename), 'r') as f:
                v_file.write(f.read())

# convert design.lvs.v to design.lvs.sp
os.chdir(work_dir)
os.system('v2lvs -i -lsp cells.sp -s cells.sp -v design.lvs.v -o design.lvs.sp')

# return to the original path
os.chdir(root_path)
