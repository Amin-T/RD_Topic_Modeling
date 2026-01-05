clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study3_V2.csv" , case(preserve) 


* Create variables
// How many risk factors are added and removed compared to the current years report
replace removed = -1*removed 
gen DiscChng = added + removed

gen nonGeneric = reported - Generics

gen logGenerics = log(Generics + 1)
gen lognonGeneric = log(nonGeneric + 1)

replace Covid_RF=. if ryear<2019
gen relCovid_RF = Covid_RF / reported

gen logCovid_RF = log(Covid_RF + 1)
gen logTotalRF = log(reported + 1)


gen Fwd_look = 0
replace Fwd_look =1 if Fu_RF/reported > Pa_RF/reported

replace rf_length = rf_length /100
gen DeltaRRLength = Delta_length/1000
replace Specificity = Specificity / rf_length

* Board and network variables
gen BoardSize = log(NumberDirectors + 1)
gen IndepDir = Independent / NumberDirectors 

gen Analysts = log(NUMBEROFANALYSTS+1)

/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

  
foreach v of varlist Volatility* {
    replace `v' = `v'*100
  } 

* RD variables
preserve
keep if ryear <= 2018
collapse (mean) reported added repeated DiscChng, by(CIK)
rename (reported added repeated DiscChng) (avgreported avgadded avgrepeated avgDiscChng)
tempfile avgfile
save `avgfile'
restore
merge m:1 CIK using `avgfile', nogen
gen TotalRF = log(avgreported +1)
gen NewRF = log(avgadded+1)
gen RepeatedRF = log(avgrepeated+1)
gen RDChng = log(avgDiscChng+1)


* Rename variables 
rename (Volatility_120 Beta_126 IndVol_ INTtA RDxopr logTA) (Volatility Beta IndVolatility Intangibles RD FirmSize)

replace COUNT_WEAK=0 if missing(COUNT_WEAK)
gen ICW = log(COUNT_WEAK+1)

replace Big4=0 if missing(Big4)

* Missing variables
drop if missing(TotalRF, NewRF, TobinQ2, ROA2, FirmSize, DtA, Current, RD, ICW, GenderRatio, BoardSize, IndepDir, Beta, Volatility, Intangibles)

// drop if ryear<2019
// drop if ryear>2022

* Drop firms with only one observations
bysort CIK: egen long cnt_obs = count(ryear)
drop if cnt_obs < 2

xtset CIK ryear
xtdescribe

* Determine control variables
global CONTROLS DeltaRRLength Beta Volatility FirmSize DtA Current RD  Intangibles ICW GenderRatio BoardSize IndepDir

winsor2 *TotalRF reported added *NewRF repeated *RepeatedRF *DiscChng *TobinQ* *ROE *ROA* NPM *Volatility *Beta *FirmSize *DtA *Current *RD *BtM ICW GenderRatio BoardSize Age IndepDir *Covid_RF Intangibles DeltaRRLength, replace


tabstat TotalRF NewRF RepeatedRF TobinQ2 ROA2 $CONTROLS, statistics(n mean sd p10 p50 p90) columns(statistics)

logout, save("Empirics3\summary4.tex") tex replace: tabstat avgreported avgadded avgrepeated Covid_RF TobinQ2 ROA2 $CONTROLS if ryear>=2019 & ryear<=2022, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
logout, save("Empirics2\summary4.rtf") word replace: tabstat avgreported avgadded avgrepeated Covid_RF TobinQ2 ROA2 $CONTROLS if ryear>=2019 & ryear<=2022, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)

logout, save("Empirics3\pwcorr4.tex") tex replace: pwcorr TotalRF NewRF RepeatedRF TobinQ2 ROA2 $CONTROLS if ryear>=2019 & ryear<=2022, star(.01) 


gen CY1 = 0
replace CY1 = 1 if ryear==2020
gen CY2 = 0
replace CY2 = 1 if ryear==2021



/*	---------- 
Main analysis
	---------- */
quietly{
	reghdfe TobinQ2 TotalRF $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M11
	
	reghdfe TobinQ2 c.TotalRF##c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M12
	
	reghdfe ROA2 TotalRF $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M13
	
	reghdfe ROA2 c.TotalRF##c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M14
}
estimates table M1*, star(.1, .05, .01) stats(N r2_a)

esttab M1* using Empirics3\Results_Total_V4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M1* using Empirics3\Results_Total_V4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 

test c.TotalRF#c.CY1 = c.TotalRF#c.CY2


* New and repeated RFs

quietly{
	reghdfe TobinQ2 NewRF RepeatedRF $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M21
	
	reghdfe TobinQ2 New Repeated CY* c.New#c.CY* c.Repeated#c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M22
	
	reghdfe ROA2 New Repeated $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M23
	
	reghdfe ROA2 New Repeated CY* c.New#c.CY* c.Repeated#c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store M24
}
estimates table M2*, star(.1, .05, .01) stats(N r2_a)

esttab M2* using Empirics3\Results_NeRep_V4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M2* using Empirics3\Results_NeRep_V4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


/*	----------
Forward looking disclosure
	---------- */

quietly{
	reghdfe TobinQ2 TotalRF c.Fwd_look##c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store A11
	
	reghdfe ROA2 TotalRF c.Fwd_look##c.CY* $CONTROLS if ryear>=2019 & ryear<=2022, absorb(SIC3) vce(cluster CIK)
	est store A12
}
estimates table A1*, star(.1, .05, .01) stats(N r2_a)

esttab A1* using Empirics3\Results_FwdLook_V4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab A1* using Empirics3\Results_FwdLook_V4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 



/*	----------
Moving average risk disclosure
	---------- */

gen avgTotalRFs = log((reported + L.reported + L2.reported)/3+1)



quietly{
	reghdfe TobinQ2 avgTotalRFs $CONTROLS, absorb(ryear SIC3) vce(cluster CIK)
	est store M11
	
	reghdfe TobinQ2 c.avgTotalRFs##c.CY* $CONTROLS, absorb(ryear SIC3) vce(cluster CIK)
	est store M12
	
	reghdfe ROA2 avgTotalRFs $CONTROLS, absorb(ryear SIC3) vce(cluster CIK)
	est store M13
	
	reghdfe ROA2 c.avgTotalRFs##c.CY* $CONTROLS, absorb(ryear SIC3) vce(cluster CIK)
	est store M14
}
estimates table M1*, star(.1, .05, .01) stats(N r2_a)

esttab M1* using Empirics3\Results_MATotal_V4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M1* using Empirics3\Results_MATotal_V4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 

test c.avgTotalRFs#c.CY1 = c.avgTotalRFs#c.CY2


/*	----------
Covid RFs
	---------- */

quietly{
	reghdfe TobinQ2 Covid_RF avgTotalRFs $CONTROLS if ryear>=2019, absorb(ryear SIC3) vce(cluster CIK)
	est store M31
	
	reghdfe ROA2 Covid_RF avgTotalRFs $CONTROLS if ryear>=2019, absorb(ryear SIC3) vce(cluster CIK)
	est store M32
}
estimates table M3*, star(.1, .05, .01) stats(N r2_a)

esttab M3* using Empirics3\Results_MACovid_V4.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M3* using Empirics3\Results_MACovid_V4.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 







