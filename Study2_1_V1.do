clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study2_data1_V2.csv" , case(preserve) 

* Create variables
// How many risk factors are added and removed compared to the current years report
replace removed = -1*removed 
gen DiscChng = added + removed
gen LogDiscChng = log(added + removed +1)
// gen leadDiscChng = log(added1 - removed1 +1)
gen leadDiscChng = added1 - removed1


gen TotalRFs = log(reported+1)
gen New = log(added+1)
gen Repeated = log(repeated+1)
gen Removed = log(removed+1)

replace Specificity = Specificity*100 / rf_length

* Board and network variables
gen BoardSize = log(NumberDirectors + 1)
gen BoardSize_1 = log(NumberDirectors_1 + 1)
gen IndepDir = Independent / NumberDirectors 
gen IndepDir_1 = Independent_1 / NumberDirectors_1 
// gen SharedDir = log(ShrdDir + 1) // log number of directors shared with other firms
gen SharedDir = ShrdDir / NumberDirectors // % directors with multi-board
gen Links = log(LnkdFirm + 1) // log number of firms linked via shared board members
// gen Tenure = log(TimeInCo+1)
gen SharedRC = ShrdRC / ShrdDir
gen SharedED = ShrdED / ShrdDir
gen FinDir = FinLink / LnkdFirm

gen Analysts = log(NUMBEROFANALYSTS+1)
gen Analysts_1 = log(NUMBEROFANALYSTS_1+1)

// replace Degree=0 if missing(Degree)
// replace Closeness=0 if missing(Closeness)
// replace Betweenness=0 if missing(Betweenness)


// * SRC with Free Float less than $75 million (Cheng, 2013)
// replace FREEFLOAT = FREEFLOAT/1000000
// gen SRC = 0
// replace SRC = 1 if FREEFLOAT < 75


/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

  
foreach v of varlist Degree Volatility* {
    replace `v' = `v'*100
  } 


* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if ryear>=2007 & ryear<=2009

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if ryear>2019

gen D_ShrdDir = (ShrdDir*100/NumberDirectors) - (ShrdDir_1*100/NumberDirectors_1)

* Missing variables
drop if missing(New, Removed, Volatility_120, Beta_126, logTA, ROE, DtA, Current, BtM, LateFiler, GenderRatio, BoardSize, RDxopr, FOG, D_ShrdDir)


replace COUNT_WEAK=0 if missing(COUNT_WEAK)
gen ICW = log(COUNT_WEAK+1)

replace Big4=0 if missing(Big4)

// * Drop firms with only one observations
// bysort CIK: egen long cnt_obs = count(ryear)
// drop if cnt_obs < 2

// * Drop banking and finance firms
// drop if inlist(FF, 45, 46, 48)

foreach v of varlist Volatility_120 Beta_126 logTA ROE DtA Current RDxopr BtM BoardSize Analysts AgeStd IndepDir {
    gen D_`v' = `v' - `v'_1
  } 

* Rename variables 
rename (Volatility_120 Beta_126 IndVol_ INTtA RDxopr logTA) (Volatility Beta IndVolatility Intangibles RD FirmSize)

* Determine control variables
global CONTROLS Volatility Beta FirmSize ROE DtA Current RD BtM LateFiler Big4 ICW GenderRatio BoardSize Analysts AgeStd IndepDir

winsor2 TotalRFs reported New Repeated Removed DiscChng LogDiscChng leadDiscChng Shared* Links Degree Volatility Beta IndVolatility FirmSize ROE DtA Current RD BtM ICW GenderRatio BoardSize InstOwnership Analysts Specificity Sentiment FOG AgeStd IndepDir D_*, replace

* Descriptive statistics of variables (after winsorizing)
tabstat TotalRFs New Removed DiscChng Specificity Sentiment FOG SharedDir Links $CONTROLS, statistics(n mean sd p10 p50 p90) columns(statistics)

// logout, save("Empirics2\summary1.tex") tex replace: tabstat reported added removed DiscChng ShrdDir LnkdFirm $CONTROLS, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
// logout, save("Empirics2\summary1.rtf") word replace: tabstat reported added removed DiscChng ShrdDir LnkdFirm $CONTROLS, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
//
// logout, save("Empirics2\pwcorr1.tex") tex replace: pwcorr stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved DVolatility DSpread Volatility30 Spread30, star(.01)

gen QVar = ShrdDir / NumberDirectors
sort QVar 
xtile deciles = QVar , n(4)
tabstat LnkdFirm reported added removed DiscChng , by(deciles) statistics(n mean)

// logout, save("Empirics2\quartiles1.tex") tex replace: tabstat ShrdDir LnkdFirm reported added removed , by(deciles) statistics(n mean) format(%9.3f)

/*

	***** Main analysis *****

	
*/
* The number of links and shared directors does not change much over the years
* --> FF fixed effects with standard errors clustered by CIK

quietly{
	reghdfe reported SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M11
	
	reghdfe DiscChng SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M13
	
	reghdfe Specificity SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M14
	
	reghdfe FOG SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M15
	
// 	reghdfe Sentiment SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
// 	est store M16
}


* Export all estimation results 
estimates table M1*, star(.1, .05, .01) stats(N r2_a)

* Estimation results to word document
esttab M1* using Empirics2\results1_ShrdDir2.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M1* using Empirics2\results1_ShrdDir2.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


* Change in the number of chared directors

gen NewDir = 0
replace NewDir = 1 if (ShrdDir-ShrdDir_1>0) & (NumberDirectors-NumberDirectors_1>0)

gen NewShrDir = 0
replace NewShrDir = 1 if ShrdDir-ShrdDir_1>0

quietly{
	reghdfe DiscChng D_ShrdDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M21
	
	reghdfe leadDiscChng D_ShrdDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M22
	
	reghdfe DiscChng NewShrDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M23
	
	reghdfe leadDiscChng NewShrDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store M24
	
// 	reghdfe DiscChng NewDir $CONTROLS if leadDiscChng!=., absorb(ryear FF) vce(cluster CIK)
// 	est store M23
//	
// 	reghdfe leadDiscChng NewDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
// 	est store M24
}

estimates table M2*, star(.1, .05, .01) stats(N r2_a)

* Estimation results to word document
esttab M2* using Empirics2\results1_Change2.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 
esttab M2* using Empirics2\results1_Change2.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 sfmt(%6.3f) 


* Test if coeficients are equal
* Statistically there is no evidence that the coefficients differ across the two models (p_value>0.05)
quietly{
	reg DiscChng D_ShrdDir $CONTROLS i.ryear i.FF
	est store M21
	reg leadDiscChng D_ShrdDir $CONTROLS i.ryear i.FF
	est store M22
	suest M21 M22, cluster(CIK)
}
test [M21_mean]D_ShrdDir = [M22_mean]D_ShrdDir

quietly{
	reg DiscChng NewShrDir $CONTROLS i.ryear i.FF
	est store M23
	reg leadDiscChng NewShrDir $CONTROLS i.ryear i.FF
	est store M24
	suest M23 M24, cluster(CIK)
}
test [M23_mean]NewShrDir = [M24_mean]NewShrDir

/*

	***** Additional analysis *****

	
*/
* Link with financial firms

// replace FinLink =1 if FinLink >0

quietly{
	reghdfe reported c.SharedDir##c.FinDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R11

	reghdfe DiscChng c.SharedDir##c.FinDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R12
	
	reghdfe Specificity c.SharedDir##c.FinDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R13
	
	reghdfe FOG c.SharedDir##c.FinDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R14
}

estimates table R1*, star(.1, .05, .01) stats(N r2_a)

* Estimation results to word document
esttab R1* using Empirics2\results1_FinLink1.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(p_f) sfmt(%6.3f) 
esttab R1* using Empirics2\results1_FinLink1.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(p_f) sfmt(%6.3f) 

* Executive directors
quietly{
	reghdfe reported c.SharedDir##c.SharedED $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R21

	reghdfe DiscChng c.SharedDir##c.SharedED $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R22
	
	reghdfe Specificity c.SharedDir##c.SharedED $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R23
	
	reghdfe FOG c.SharedDir##c.SharedED $CONTROLS, absorb(ryear FF) vce(cluster CIK)
	est store R24
}

estimates table R2*, star(.1, .05, .01) stats(N r2_a)



* Robustness: DiscChng does not capture the change in risk disclosure length
replace rf_length = rf_length /1000
replace Delta_length = Delta_length*100 / (rf_length - Delta_length)
winsor2 rf_length Delta_length, replace

reghdfe Delta_length SharedDir $CONTROLS, absorb(ryear FF) vce(cluster CIK)


* Create lag variable for successive years
sort CIK ryear
by CIK: gen lagNew = New[_n-1] if ryear==ryear[_n-1]+1

generate date = date(report_dt, "YMD")
format %td date

