clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study2_data2_V2.csv", case(preserve) 

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

gen Analysts = log(NUMBEROFANALYSTS+1)

replace Specificity = Specificity*100 / RF_length

gen D_length = (RF_length / (length_1+1))-1

replace RF_length = RF_length / 1000

gen D_IndDisc = IndDisc - IndDisc_1

// replace at = at/1000 // to billion
// replace mkvalt = mkvalt/1000


// * max number of disclosures per cik per topic_h over the years
// by CIK Topic_H, sort: egen max_disc = max(DiscSum)
// drop if max_disc<=0
//
// by CIK Topic_H, sort: egen min_disc = min(DiscSum)
// drop if min_disc>=2


* Board and network variables
gen BoardSize = log(NumberDirectors + 1)
gen SharedDir = log(ShrdDir + 1) // log number of directors shared with other firms
gen Links = log(LnkdFirm + 1) // log number of firms linked via shared board members
gen RiskDir = log(ShrdRiskDir +1)
gen SharedED = log(ShrdED +1)
gen FinDir = log(FinLink +1)
gen LnkDisc_r = LnkDisc / LnkdFirm


* Missing variables
drop if missing(Volatility_120, Beta_126, logTA, ROE, DtA, Current, BtM, LateFiler, GenderRatio, BoardSize, RDxopr, FOG)

replace COUNT_WEAK=0 if missing(COUNT_WEAK)
gen ICW = log(COUNT_WEAK+1)

replace Big4=0 if missing(Big4)


// * Drop firms with only one year of obsrvation
// by CIK fyear, sort: gen nvals = _n == 1
// by CIK, sort: egen long cnt_obs = sum(nvals)
// drop if cnt_obs < 2
//
// * Drop banking and finance firms
// drop if inlist(FF, 45, 46, 48)


* Rename variables 
rename (Volatility_120 Beta_126 IndVol_ INTtA RDxopr logTA) (Volatility Beta IndVolatility Intangibles RD FirmSize)


* Determine control variables
global CONTROLS D_IndDisc Volatility Beta IndVolatility FirmSize ROE DtA Current RD BtM Big4 ICW GenderRatio Analysts BoardSize


foreach v of varlist LnkDisc OldLnkNewDisc NewLnkLstyrDisc NewLnkRepDisc {
    replace `v' = 0 if missing(`v')
	
	gen `v'_d = 0
	replace `v'_d =1 if `v'>0
	
	gen log`v' = log(`v' + 1)
} 


winsor2 *LnkDisc *OldLnkNewDisc *NewLnkLstyrDisc *NewLnkRepDisc IndDisc D_IndDisc Volatility* IndVolatility FirmSize ROE DtA Current RD BtM ICW GenderRatio Analysts BoardSize RF_length Specificity, replace



/*

	***** Main analysis *****

	
*/
* The number of linked firms is rather constant over the years for individual firms --> no firm fixed effect
quietly{
	logistic Disclosed LnkDisc_d LstYrDisc $CONTROLS i.Topic_H i.ryear i.FF, vce(cluster CIK) coef
	est store M11
	
	logistic New LnkDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store M12
	
	* Firm A is more likly to add RT if a firm linked for more than 1 year adds same RT in same year
	logistic New OldLnkNewDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store M13
	
	*Firm A is likely to add RT after it connects to firm B who has disclosed RT last year
	logistic New NewLnkLstyrDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store M14
	
	logistic Removed LnkDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==1, vce(cluster CIK) coef
	est store M15
}

* Export all estimation results 
estimates table M1*, drop(i.Topic_H i.ryear i.FF) star(.1, .05, .01) stats(N r2_p)


* Estimation results to word document
esttab M1* using Empirics2\results2_LnkdDisc1.rtf, nogaps drop(*Topic_H *ryear *FF) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_p) sfmt(%6.3f) 
esttab M1* using Empirics2\results2_LnkdDisc1.tex, drop(*Topic_H *ryear *FF) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_p) sfmt(%6.3f) 


* Firm is more linkely to remove if the new linked firms are not disclosing
logistic Removed NewLnkRepDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==1 & D_LnkdFirm>0, vce(cluster CIK) coef


* Effect of disclosure by linked firms on RF attribuates (Quality)

quietly{
	reghdfe Specificity LnkDisc $CONTROLS if Disclosed==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M21
	
	reghdfe FOG LnkDisc $CONTROLS if Disclosed==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M22
	
	reghdfe RF_length LnkDisc $CONTROLS if Disclosed==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M23
}

estimates table M2*, star(.1, .05, .01) stats(N r2_a)


* Estimation results to word document
esttab M2* using Empirics2\results2_RTattributes1.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 
esttab M2* using Empirics2\results2_RTattributes1.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 


/*

	***** Additional analysis *****
	
*/


* plot logitic model predictions
// predict newvar1
// scatter newvar1 rel_disclnkdfrm, sort mcolor(%20) msize(tiny) mlcolor(none) jitter(5)



* Informativeness

global CONTROLS2 Sentiment RF_length IndDisc Volatility Beta IndVolatility FirmSize ROE DtA Current RD BtM Big4 ICW GenderRatio Analysts LateFiler

quietly{
	reghdfe Volatility60 Added Repeated LnkDisc c.Added#c.LnkDisc c.Repeated#c.LnkDisc $CONTROLS2, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M31
	
	reghdfe Volatility60 Added Repeated $CONTROLS2 if LnkDisc>0, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M32
	
	reghdfe Volatility60 Added Repeated $CONTROLS2 if LnkDisc==0, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M33
}

estimates table M3*, star(.1, .05, .01) stats(N r2_a)

esttab M2* using Empirics2\results2_Info1.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 
esttab M2* using Empirics2\results2_Info1.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 



graph box LnkdDisc, over(Disclosed, gap(50)) nooutsides alsize(50) ytitle("Mean of LnkdDisc")

