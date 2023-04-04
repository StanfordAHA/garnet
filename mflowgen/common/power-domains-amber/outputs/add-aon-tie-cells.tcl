setVar spgAddTieForNonDefPDFTerms 1
setTieHiLoMode -cell $ADK_TIE_CELLS
foreach cell $ADK_TIE_CELLS {
   setDontUse $cell false
}
addTieHiLo -powerDomain AON -matchingPDs true

foreach cell $ADK_TIE_CELLS {
   setDontUse $cell true
}

