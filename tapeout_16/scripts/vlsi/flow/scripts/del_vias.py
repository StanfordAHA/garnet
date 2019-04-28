
import sys

areas = []
with open(sys.argv[1], 'r') as f:
  linem2 = ''
  linem1 = '' 
  for line in f.readlines():
    if 'Same Layer Cut Spacing' in line:
      s = line.split(':')
      if len(s) > 5:
        obj1 = s[4].split(' ')
        del obj1[-1]
        obj1 = ' '.join(obj1)
        obj1 = obj1.strip()
        obj2 = s[5].split(' ')
        del obj2[-1]
        obj2 = ' '.join(obj2)
        obj2 = obj2.strip()
        if 'VDD' in linem1 or 'VSS' in linem1 or 'VDD' in linem2 or 'VSS' in linem2:
          uy = obj1.split(' ')[3].translate(None,'.')
          if ((int(uy)+2240))%5760 == 0:
            areas.append(obj1.strip())
          uy = obj2.split(' ')[3].translate(None,'.')
          if ((int(uy)+2240))%5760 == 0:
            areas.append(obj2.strip())
    linem2 = linem1
    linem1 = line



with open('del_vias.tcl', 'w') as f:
  f.write('set delcount 0\n')
  f.write('puts "Deleting vias. Please wait..."\n')
  for area in areas:
    f.write('''
foreach v [get_obj_in_area -area { %s } -obj_type speical_via] {
  if {[string match "VIAGEN12_*" [get_db [get_db $v .via_def] .name]]} { 
    #puts "Deleting via at %s"
    delete_obj $v 
    set delcount [expr $delcount+1]
  }
}
'''%(area, area))
  f.write('puts "Deleted a total of $delcount vias"\n')
