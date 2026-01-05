clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study2_data3_V6.csv", case(preserve) 


* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if ryear>=2007 & ryear<=2009

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if ryear>2019

* Create variables
gen TotalRFs = log(reported+1)
gen TotalRFs_2 = log(reported_2+1)

* Board and network variables
gen BoardSize = log(NumberDirectors + 1)
gen BoardSize_2 = log(NumberDirectors_2 + 1)
gen Links = log(LnkdFirm + 1 - Linked) // log number of firms linked via shared board members
gen Links_2 = log(LnkdFirm_2 + 1 - Linked) // log number of firms linked via shared board members
gen IndepDir = Independent / NumberDirectors 
gen IndepDir_2 = Independent_2 / NumberDirectors_2

gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

gen LateFiler_2 = 0
replace LateFiler_2 = 1 if rfGap_2 >= 75

foreach v of varlist Volatility* {
    replace `v' = `v'*100
  } 

replace rf_length = rf_length/1000
replace rf_length_2 = rf_length_2/1000
  
replace COUNT_WEAK=0 if missing(COUNT_WEAK)
replace Big4=0 if missing(Big4)
gen ICW = log(COUNT_WEAK+1)

replace COUNT_WEAK_2=0 if missing(COUNT_WEAK_2)
replace Big4_2=0 if missing(Big4_2)
gen ICW_2 = log(COUNT_WEAK_2+1)

* Create pair comparison variables
gen SameInd = 0
replace SameInd = 1 if FF == FF_2

gen SameAud = 0
replace SameAud = 1 if AUDITOR_FKEY == AUDITOR_FKEY_2

gen Analysts = log(NUMBEROFANALYSTS+1)
gen Analysts_2 = log(NUMBEROFANALYSTS_2+1)

global FIRMVARS TotalRFs rf_length Links Volatility_120 Beta_126 IndVol_ at ROE DtA Current RDxopr BtM ICW GenderRatio BoardSize Analysts Age IndepDir TotCurrBrd 


foreach v of varlist $FIRMVARS {
//     gen pair`v' = (`v'+`v'_2)/2
	gen pair`v' = abs(`v'-`v'_2)
  } 

gen pairFirmSize = log(pairat+1)


* Rename variables 
rename (pairVolatility_120 pairBeta_126 pairIndVol_ pairRDxopr) (pairVolatility pairBeta IndVolatility pairRD)

* Determine control variables
global CONTROLS pairTotalRFs pairLinks pairVolatility pairBeta pairFirmSize pairROE pairDtA pairCurrent pairRD pairBtM pairICW pairGenderRatio pairAnalysts pairAge pairIndepDir pairTotCurrBrd SameAud //pairBoardSize

winsor2 SharedRF pairTotalRFs pairLinks pairVolatility pairBeta pairFirmSize pairROE pairDtA pairCurrent pairRD pairBtM pairICW pairGenderRatio pairAnalysts pairBoardSize pairAge pairIndepDir pairTotCurrBrd, replace

egen pair_id = group(CIKpair_ID)

replace ED=0 if missing(ED)
replace RiskCommittee=0 if missing(RiskCommittee)
replace AuditCommittee=0 if missing(AuditCommittee )

duplicates drop pair_id ryear, force

by CIKpair_ID, sort: egen sumLinked = sum(Linked)
drop if Treatment=="True" & sumLinked==0


/*** Stacked event study estimator ***/
gen Treated = 0
replace Treated = 1 if Treatment == "True"

gen no_Treated=0
replace no_Treated=1 if Treatment=="False"

* Creating leads and lags
gen time_to_event = ryear - eventX + 1
replace time_to_event =0 if Treatment=="False" | missing(eventX)

gen FirstTimeLinked = Linked == 1 & ryear == eventX

keep if inrange(time_to_event, -3, 6)

* Drop firm-pairs with only one observations
bysort CIKpair_ID: egen long cnt_obs = count(ryear)
drop if cnt_obs < 5

// logout, save("Empirics2\interlock_summary2.tex") tex replace: tabstat Linked FirstTimeLinked if Treatment =="True", by(ryear) statistics(n mean sd) columns(statistics)


* Post treatment
forvalues i = 3(-1)1 {
    gen Pre`i'=0
	replace Pre`i'=1 if time_to_event==-`i'
}

gen ref=0
replace ref=1 if time_to_event==0

* Post treatment
forvalues i = 1/6 {
    gen Post`i'=0
	replace Post`i'=1 if time_to_event==`i'
}

ebalance Treated $CONTROLS

// logout, save("Empirics2\ebalance2.tex") tex replace: ebalance Treated $CONTROLS

tabstat SharedRF, by(Treatment) statistics(mean variance skewness)

egen preSum = rowtotal(Pre*)

egen postSum = rowtotal(Post*)


// logout, save("Empirics2\pwcorr3.tex") tex replace: pwcorr SharedRF preSum postSum ED RiskCommittee AuditCommittee $CONTROLS, star(.01)


/*

	***** Main analysis *****

	
*/

quietly{
	preserve
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore

	est store DiD1


	preserve
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates(ED RiskCommittee AuditCommittee $CONTROLS) interact_cov("yes")
	restore

	est store DiD2
	
	
	preserve
	stackedev SharedRF preSum postSum ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore

	est store DiDAE1


	preserve
	stackedev SharedRF preSum postSum ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates(ED RiskCommittee AuditCommittee $CONTROLS) interact_cov("yes")
	restore

	est store DiDAE2
}

* Export all estimation results 
estimates table DiD*, star(.1, .05, .01) stats(N r2_a)

esttab DiD1 DiDAE1 using Empirics2\results3_BakerDiD4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab DiD1 DiDAE1 using Empirics2\results3_BakerDiD4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


esttab DiD2 DiDAE2 using Empirics2\results3_DiDDirType4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab DiD2 DiDAE2 using Empirics2\results3_DiDDirType4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 

/*

	***** Additional analysis *****
	
*/

quietly{
	preserve
	keep if SameInd == 0
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore
	est store R11
	
	preserve
	keep if SameInd == 1
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore
	est store R12
}


* Export all estimation results 
estimates table R1*, star(.1, .05, .01) stats(N r2_a)

esttab R1* using Empirics2\results3_AddInd3.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab R1* using Empirics2\results3_AddInd3.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


* Litigation risk
quietly{
	preserve
	keep if high_litigation ==1 & high_litigation_2 ==1
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore

	est store R21


	preserve
	keep if high_litigation ==0 & high_litigation_2 ==0
	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
	restore

	est store R22
	
	
// 	preserve
// 	keep if high_litigation != high_litigation_2
// 	stackedev SharedRF Pre* Post* ref [pweight=_webal], cohort(eventX) time(ryear) never_treat(no_Treated) unit_fe(pair_id) clust_unit(pair_id) covariates($CONTROLS) interact_cov("yes")
// 	restore
//
// 	est store R23
}

* Export all estimation results 
estimates table R2*, star(.1, .05, .01) stats(N r2_a)

esttab R2* using Empirics2\results3_litigation.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab R2* using Empirics2\results3_litigation.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 



* Crisis and non-crisis years
quietly{
	reghdfe SharedRF Linked c.Linked#c.ED c.Linked#c.RiskCommittee c.Linked#c.AuditCommittee $CONTROLS if ryear<2010, absorb(FF FF_2 ryear) vce(cluster CIKpair_ID) keepsingletons
	est store R31
	
	reghdfe SharedRF Linked c.Linked#c.ED c.Linked#c.RiskCommittee c.Linked#c.AuditCommittee $CONTROLS if ryear>=2010, absorb(FF FF_2 ryear) vce(cluster CIKpair_ID) keepsingletons
	est store R32
}

* Export all estimation results 
estimates table R3*, star(.1, .05, .01) stats(N r2_a)

esttab R3* using Empirics2\results3_Addcrisis.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab R3* using Empirics2\results3_Addcrisis.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 

quietly{
	reg SharedRF Linked c.Linked#c.ED c.Linked#c.RiskCommittee c.Linked#c.AuditCommittee $CONTROLS i.ryear i.FF i.FF_2 if ryear<2010
	est store R31
	reg SharedRF Linked c.Linked#c.ED c.Linked#c.RiskCommittee c.Linked#c.AuditCommittee $CONTROLS i.ryear i.FF i.FF_2 if ryear=>2010
	est store R32
	suest R31 R32, cluster(CIKpair_ID)
}
test [R31_mean]Linked = [R32_mean]Linked



