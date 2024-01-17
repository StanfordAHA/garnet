// $Log$
//
// 2020-11-12 17:25:19 f7e2fe8b0 Remove in-file logs
// 2019-08-16 16:16:39 e61208845 hsdes 2208188037 ; support for b88xp_nrfhyp160 b88xp_nrfhyp120 device new list of pcells rfhyppcells ; ensure they are kept
// 2018-05-09 08:52:48 abc206f9f remove b88xp_dcps2p_unit since not needed ; already covered by b88xp_dcps2p
// 2018-05-08 18:47:00 786bf7dd1 hsdes1407079382 ; need to explicitly prevent b88xp_mfc_unit and b88xp_dcps2p_unit from exploding (the 2017.12 has built in functionality that enables texted_with to work correctly)
// 2018-03-06 10:38:25 88b500528 hsd 1406873754 ; optimize hierarchy_auto_options for trclvs performance ; control hao moved to proj_config/user_runOptions ; protect the AD pcells with no_explode ; can revert to previous methodology/settings with _drHAO_HISTORIC
// 2015-11-11 17:32:55 d039fe47e fix syntax added a missing closing paren
// 2015-11-10 11:42:17 79ab2d715 hsd 4092 ; if _drRCextractUnimp set containers2Explode to an empty list
// 2015-11-02 22:20:05 5e462aa65 copied from 1222
//

#include <include/userProject_cellListsTRC.rh>

#ifndef _USERPROJECT_CELLLISTSTRC_RS_
#define _USERPROJECT_CELLLISTSTRC_RS_

#if (defined(_drRCextractUnimp))
   containers2Explode = {};
#else
   // list of known layout only cells / via and containers
   containers2Explode = {"*_fill", "*_filler", "*_cont", "*_halo", "*mfill", "\$\$*"};
#endif

// oaConstructs
// based upon 2.60 techfile
oaConstructs2Explode = {
"vcnaxv",
"vcnaxv_3",
"vcnaxh",
"vcnaxh_3",
"v0ax",
"v0ax_2",
"v1a",
"v1a_3",
"v2a",
"v2a_2",
"v2a_3",
"v2a_4",
"v3a",
"v3a_2",
"v4a",
"v5as",
"v6as",
"v7as",
"v8s",
"v9s",
"v10s",
"v11a",
"tv1a",
"ndiff_diffcon",
"pdiff_diffcon",
"diffcon_polycon",
"poly_polycon",
"metal0_metalc0",
"metal2_metalc2",
"metal3_metalc3",
"ip224uhdlp1p11rf_512x32m4b2c1s0_t0r0p0d0a1m1h_c2229srstsphdclp_cssatimctrlmid",
"ip224uhdlp1p11rf_4096x64m4b2c1s1_t0r0p0d0a1m1h_c2229srstsphdclp_cssatimctrlmid",
"ip224uhdlp1p11rf_8192x32m8b2c1s1_t0r0p0d0a1m1h_c2229srstsphdclp_cssatimctrlmid",
"gpio_1v2_e1__sdio1v8_logic"
};

explode_list = strcat(strcat(explode_list, containers2Explode), oaConstructs2Explode);

// constructs to preserve
// pcells that wont normally be picked up by schematic subckt match
constructs2Save:list of string = {
    // PCELLS ; need construction check in TemplateUsage
     // TFR/MFC pcell temmplates 
     "*b88xp_dcpstack[_$]*", "*b88xp_dcps2p[_$]*", 
     "*b88xp_mfcs2g[_$]*", "*b88xp_mfcs2p[_$]*", "*b88xp_mfcs2s[_$]*", 
     "*b88xp_mfcs2sds[_$]*", "*b88xp_mfcs2sls[_$]*", 
     "*cap_hd_CDNS[_$]*",
     // needed for 2017.06 and before versions to stop unit from exploding 2017.12 internally has text preserve for texted_with operations
     "*b88xp_mfc_unit[_$]*",
     // note *b88xp_tfr* will glob all of these + the _dnw versions (so tfr_fill tfrdacbody trfdaccon not really needed)
     "*b88xp_tfr*", "*b88xp_tfr_fill*", "*b88xp_tfrdacbody*", "*b88xp_tfrdaccon*", 

     // rpoly resistor
     "*b88xp_poly[_$]*", "*b88xp_polynwl[_$]*",  // iso 
     "*b88xp_polyser[_$]*", "*b88xp_polysernwl[_$]*", // series
     "*b88xp_polypara[_$]*", "*b88xp_polyparanwl[_$]*", // parallel

     // rgcn resistor
     "*b88xp_gcn[_$]*", "*b88xp_gcnnwl[_$]*",  // iso 
     "*b88xp_gcnser[_$]*", "*b88xp_gcnsernwl[_$]*", // series
     "*b88xp_gcnpara[_$]*", "*b88xp_gcnparanwl[_$]*", // parallel

     // EDMOS
      "*b88x_ednrf[_$]*",  "*b88x_edprf[_$]*",   // now parent cells

      // Inductors
      "*b88xp_ind3t[_$]*",  "*b88xp_ind2t[_$]*",

     // hyp cells
     "*b88xp_nrfhyp120[_$]*", "*b88xp_nrfhyp160[_$]*",

};

no_explode_list = no_explode_list.merge(constructs2Save);

#endif // _USERPROJECT_CELLLISTSTRC_RS_

