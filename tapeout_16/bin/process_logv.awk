#!/usr/bin/awk -f

# IN:   "[10/08 18:40:13  25696s] @file_info: - M1 Stripes Complete"
# OUT:  "[10/08 18:40     120h44] @file_info: - M1 Stripes Complete"

/^.[0-9][0-9].[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9] / {
    mon = substr($0,  2, 2)
    day = substr($0,  5, 2)
    hr  = substr($0,  8, 2)
    min = substr($0, 11, 2)

    if (GOT_ZERO == "") {
        zmon = mon # unused
        zday = day
        zhr  = hr  # unused
        zmin = 60*hr + min
        printf("%s %s %s %s\n", zmon, zday, zhr, zmin)
        GOT_ZERO = "true"
    }
    if (day != zday) {
        zday = day
        zmin = zmin - (24*60)
    }
    nmins = (hr*60 + min) - zmin
    time = sprintf("\\1%4dh%02d", nmins/60, nmins%60)

    # "[10/08 18:40:13  25696s] @file_info: - M1 Stripes Complete" =>
    # "[10/08 18:40     25696s] @file_info: - M1 Stripes Complete"
    $0 =     gensub(/^(.[0-9][0-9].[0-9][0-9] [0-9][0-9]:[0-9][0-9]):[0-9][0-9] /,
           "\\1 ", "g", $0)


    # "[10/08 18:40  25696s] @file_info: - M1 Stripes Complete" =>
    # "[10/08 18:40   7h08m] @file_info: - M1 Stripes Complete"
    $0 = gensub(/([0-9] ) *[0-9]*s/, time, "g",$0)
}
{ print $0 }
