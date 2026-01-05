clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study2_data2_V3.csv", case(preserve) 

/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

  
foreach v of varlist Degree Volatility* IndDisc {
    replace `v' = `v'*100
  } 


* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if ryear>=2007 & ryear<=2009

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if ryear>2019

gen Analysts = log(NUMBEROFANALYSTS+1)

// replace Specificity = Specificity*100 / RF_length // done in Python code

gen D_length = (RF_length / (length_1+1))-1

// replace RF_length = RF_length / 1000

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
gen IndepDir = Independent / NumberDirectors 
gen SharedDir = log(ShrdDir + 1) // log number of directors shared with other firms
gen Links = log(LnkdFirm + 1) // log number of firms linked via shared board members
gen SharedRC = ShrdRC / ShrdDir
gen SharedED = ShrdED / ShrdDir
gen SharedAC = ShrdAC / ShrdDir
gen FinDir = FinLink / LnkdFirm

// replace TotCurrBrd = log(TotCurrBrd + 1)


* Missing variables
drop if missing(Volatility_120, Beta_126, logTA, ROE, DtA, Current, BtM, LateFiler, GenderRatio, BoardSize, RDxopr, ShrdDir, ShrdDir_1, TotCurrBrd, Age)

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
rename (Volatility_120 Beta_126 IndVol_ INTtA RDxopr logTA RR_len_1) (Volatility Beta IndVolatility Intangibles RD FirmSize Item1ALen)


* Determine control variables
global CONTROLS IndDisc Volatility Beta GenderRatio BoardSize Age IndepDir TotCurrBrd FirmSize ROE DtA Current RD BtM Big4 ICW Analysts


foreach v of varlist LnkDisc OldLnkNewDisc NewLnkLstyrDisc LnkLstyrDisc {
    replace `v' = 0 if missing(`v')
	
	gen `v'_d = 0
	replace `v'_d =1 if `v'>0
	
// 	gen log`v' = log(`v' + 1)
} 

replace RF_length = RF_length /100
replace meanLen = meanLen /100
replace Item1ALen = Item1ALen /100

replace Specificity = Specificity / RF_length
replace meanSpec = meanSpec*100

gen Item1ASpec = Specificity_1/Item1ALen

winsor2 *LnkDisc *OldLnkNewDisc *NewLnkLstyrDisc *LnkLstyrDisc *IndDisc Volatility* IndVolatility FirmSize ROE DtA Current RD BtM ICW GenderRatio Analysts BoardSize RF_length Specificity* FOG Item1AFOG_1 Age* IndepDir meanSpec meanFOG meanLen Item1ASpec Item1ALen TotCurrBrd TotalRFs Shared*, replace

rename (Specificity FOG RF_length LnkLstyrDisc_d meanSpec Item1ASpec meanFOG Item1AFOG_1 meanLen Item1ALen) (RFSpec RFFog RFLen LinkDisc_t_1 InterlockSpec Item1ASpec InterlockFog Item1AFog InterlockLen Item1ALen)

// logout, save("Empirics2\summaryTIJA.rtf") word replace: tabstat RFSpec RFFog RFLen LinkDisc_t_1 InterlockSpec InterlockFog InterlockLen IndDisc if New==1, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
// logout, save("Empirics2\summaryTIJA.tex") tex replace: tabstat RFSpec RFFog RFLen LinkDisc_t_1 InterlockSpec InterlockFog InterlockLen IndDisc if New==1, statistics(n mean sd p10 p50 p90) columns(statistics)

logout, save("Empirics2\pwcorr1.tex") tex replace: pwcorr RFSpec RFFog RFLen LinkDisc_t_1 InterlockSpec Item1ASpec InterlockFog Item1AFog InterlockLen Item1ALen $CONTROLS if New==1, star(.01)

replace meanLen=0 if missing(meanLen)
replace meanFOG=0 if missing(meanFOG)
replace meanSpec=0 if missing(meanSpec)


/*

	***** Main analysis *****

	
*/

* Effect of disclosure by linked firms on RF attribuates (Quality)

quietly{	
	reghdfe Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS if New==1, absorb(ryear Topic_H FF) vce(cluster CIK)	
	est store M21
	
	reghdfe FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS if New==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M22
	
	reghdfe RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS if New==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store M23
}

estimates table M2*, star(.1, .05, .01) stats(N r2_a)


* Estimation results to word document
esttab M2* using Empirics2\results2_RTattributes5.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 
esttab M2* using Empirics2\results2_RTattributes5.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 



/*

	***** Additional analysis *****
	
*/


* plot logitic model predictions
// predict newvar1
// scatter newvar1 rel_disclnkdfrm, sort mcolor(%20) msize(tiny) mlcolor(none) jitter(5)


* The number of linked firms is rather constant over the years for individual firms --> no firm fixed effect
quietly{
	* Firm A is more likly to add RT if a firm linked for more than 1 year adds same RT in same year
	logistic New LnkDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store R11
	
	logistic New OldLnkNewDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store R12
	
	*Firm A is likely to add RT after it connects to firm B who has disclosed RT last year
	logistic New NewLnkLstyrDisc_d $CONTROLS i.Topic_H i.ryear i.FF if LstYrDisc==0, vce(cluster CIK) coef
	est store R13
}

* Export all estimation results 
estimates table R1*, drop(i.Topic_H i.ryear i.FF) star(.1, .05, .01) stats(N r2_p)


* Estimation results to word document
esttab R1* using Empirics2\results2_Robust2.rtf, nogaps drop(*Topic_H *ryear *FF) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_p) sfmt(%6.3f) 
esttab R1* using Empirics2\results2_Robust2.tex, nogaps drop(*Topic_H *ryear *FF) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_p) sfmt(%6.3f) 



quietly{
	reghdfe Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS if New==1 & ryear<=2010, absorb(ryear Topic_H FF) vce(cluster CIK)	
	est store R21
	
	reghdfe FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS if New==1 & ryear<=2010, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R22
	
	reghdfe RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS if New==1 & ryear<=2010, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R23
	
	reghdfe Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS if New==1 & ryear>2010, absorb(ryear Topic_H FF) vce(cluster CIK)	
	est store R24
	
	reghdfe FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS if New==1 & ryear>2010, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R25
	
	reghdfe RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS if New==1 & ryear>2010, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R26
}

estimates table R2*, star(.1, .05, .01) stats(N r2_a)

esttab R2* using Empirics2\results2_Addcrisis2.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 
esttab R2* using Empirics2\results2_Addcrisis2.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 


* Litigation risk
quietly{
	reghdfe Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS if New==1 & high_litigation==1, absorb(ryear Topic_H FF) vce(cluster CIK)	
	est store R31
	
	reghdfe FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS if New==1 & high_litigation==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R32
	
	reghdfe RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS if New==1 & high_litigation==1, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R33
	
	reghdfe Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS if New==1 & high_litigation==0, absorb(ryear Topic_H FF) vce(cluster CIK)	
	est store R34
	
	reghdfe FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS if New==1 & high_litigation==0, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R35
	
	reghdfe RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS if New==1 & high_litigation==0, absorb(ryear Topic_H FF) vce(cluster CIK)
	est store R36
}

estimates table R3*, star(.1, .05, .01) stats(N r2_a)

esttab R3* using Empirics2\results2_litigation.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 
esttab R3* using Empirics2\results2_litigation.tex, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(r2_a) sfmt(%6.3f) 

* Test if coeficients are equal
* The coeficient in model R21 is significantly larger than tha in model R22 (p_value<0.05)
quietly{
	reg Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==1
	est store T1
	reg Specificity LnkLstyrDisc_d meanSpec Item1ASpec $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==0
	est store T2
	suest T1 T2, cluster(CIK)
}
test [T1_mean]LnkLstyrDisc_d = [T2_mean]LnkLstyrDisc_d

quietly{
	reg FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==1
	est store T1
	reg FOG LnkLstyrDisc_d meanFOG Item1AFOG_1 $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==0
	est store T2
	suest T1 T2, cluster(CIK)
}
test [T1_mean]LnkLstyrDisc_d = [T2_mean]LnkLstyrDisc_d

quietly{
	reg RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==1
	est store T1
	reg RF_length LnkLstyrDisc_d meanLen Item1ALen $CONTROLS i.ryear i.Topic_H ib1.FF if New==1 & high_litigation==0
	est store T2
	suest T1 T2, cluster(CIK)
}
test [T1_mean]LnkLstyrDisc_d = [T2_mean]LnkLstyrDisc_d

