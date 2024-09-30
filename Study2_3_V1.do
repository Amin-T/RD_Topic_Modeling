clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study2_data3_V2.csv", case(preserve) 


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
gen Links = log(LnkdFirm + 1) // log number of firms linked via shared board members
gen Links_2 = log(LnkdFirm_2 + 1) // log number of firms linked via shared board members


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

gen Analysts = log(NUMBEROFANALYSTS+1)
gen Analysts_2 = log(NUMBEROFANALYSTS_2+1)

global FIRMVARS TotalRFs rf_length Links Volatility_120 Beta_126 IndVol_ at ROE DtA Current RDxopr BtM LateFiler Big4 ICW GenderRatio BoardSize Analysts


foreach v of varlist $FIRMVARS {
    gen `v'_p = (`v'+`v'_2)/2
  } 

gen FirmSize = log(at_p)


* Rename variables 
rename (Volatility_120_p Beta_126_p IndVol__p RDxopr_p) (Volatility Beta IndVolatility RD)

* Determine control variables
global CONTROLS TotalRFs_p Links_p Volatility Beta IndVolatility FirmSize ROE_p DtA_p Current_p RD BtM_p LateFiler_p Big4_p ICW_p GenderRatio_p Analysts_p // SameInd BoardSize_p 

winsor2 SharedRF TotalRFs_p rf_length_p Links_p Volatility Beta IndVolatility FirmSize ROE_p DtA_p Current_p RD BtM_p LateFiler_p Big4_p ICW_p GenderRatio_p BoardSize_p Analysts_p, replace

// encode CIKpair_ID , generate(ID)

drop FinLink*
gen FinLink = 0
replace FinLink = 1 if inlist(FF, 45, 46, 48) | inlist(FF_2, 45, 46, 48)

replace ED=0 if missing(ED)
replace RiskCommittee=0 if missing(RiskCommittee)


/*

	***** Main analysis *****

	
*/

* two-way fixed effects difference-in-differences (DID) model
quietly{
	reghdfe SharedRF Linked $CONTROLS, absorb(CIKpair_ID ryear) vce(cluster CIKpair_ID) keepsingletons
	est store M11
	
	reghdfe SharedRF c.Linked##c.FinLink $CONTROLS, absorb(CIKpair_ID ryear) vce(cluster CIKpair_ID) keepsingletons
	est store M12
	
	reghdfe SharedRF ED $CONTROLS, absorb(CIKpair_ID ryear) vce(cluster CIKpair_ID) keepsingletons
	est store M13
	
	reghdfe SharedRF RiskCommittee $CONTROLS, absorb(CIKpair_ID ryear) vce(cluster CIKpair_ID) keepsingletons
	est store M14
}

* Export all estimation results 
estimates table M1*, star(.1, .05, .01) stats(N r2_a)

esttab M1* using Empirics2\results3_ShrdRFs1.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M1* using Empirics2\results3_ShrdRFs1.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


// gen Treated = 0
// replace Treated =1 if Treatment == "True"
// gen DiD = Linked * Treated

// gen eventX = .
// replace eventX = ryear if LinkTime == 1
// bysort CIKpair_ID (eventX): replace eventX = eventX[_n-1] if missing(eventX)
// bysort CIKpair_ID (eventX): replace eventX = eventX[_n+1] if missing(eventX)
gen time_to_event = ryear - eventX

drop if time_to_event < -10
drop if time_to_event > 10 & time_to_event != .

eventdd SharedRF $CONTROLS, hdfe absorb(CIKpair_ID ryear) vce(cluster CIKpair_ID) timevar(time_to_event) graph_op(xlabel(-5(1)6, labsize(3))) ci(rarea, color(gs14%33)) leads(5) lags(6) accum


