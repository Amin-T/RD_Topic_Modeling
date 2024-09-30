clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\study1_data2_V4.csv", case(preserve) // BASpreaad with CLOSEPRICE

/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

* SRC with Free Float less than $75 million (Cheng, 2013)
replace FREEFLOAT = FREEFLOAT/1000000
gen SRC = 0
replace SRC = 1 if FREEFLOAT < 75

* Scale up dependent variables
foreach v of varlist Volatility* Spread*{
    replace `v' = `v'*100
  } 

replace at = at/1000 // to billion
replace mkvalt = mkvalt/1000

replace SHRTURN = SHRTURN*100

replace RF_length = D_length if RF_length==0
replace RF_length = RF_length /1000

replace ActEst = ActEst /EarningsPerShareActual
replace ActEst_before = ActEst_before /EarningsPerShareActual

* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if ryear>=2007 & ryear<=2009

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if ryear>2019


* Generate dependent variables
gen DVolatility = (Volatility30 - Volatility_30)*100/Volatility_30
gen DSpread = (Spread30 - Spread_30)*100/Spread_30

gen DSHRTURN = (SHRTURN5 - SHRTURN_5)*100/SHRTURN_5


* max number of disclosures per cik per topic_h over the years
by CIK Topic_H, sort: egen max_disc = max(DiscSum)
drop if max_disc<=0

by CIK Topic_H, sort: egen min_disc = min(DiscSum)
drop if min_disc>=2


* Drop missing variables
drop if missing(SHRTURN, ROE, DtA, current, INTtA, BtM, NUMBEROFANALYSTS, Beta_120, firms, LateFiler, IndVol_, RDxopr, D_length, FREEFLOAT, DVolatility, DSpread, RF_length, Volatility_120, Spread_120)

replace COUNT_WEAK=0 if missing(COUNT_WEAK)
replace Big4=0 if missing(Big4)

gen ICW = log(COUNT_WEAK+1)

* Drop firms with only one year of obsrvation
by CIK fyear, sort: gen nvals = _n == 1
by CIK, sort: egen long cnt_obs = sum(nvals)
drop if cnt_obs < 2

* Rename variables 
rename (RF_length Volatility_120 Spread_120 Beta_120 IndVol_ SHRTURN current INTtA NUMBEROFANALYSTS firms RDxopr CategoryPercentOfTradedShares ) (RFLength Volatility Spread Beta IndVolatility ShrTurn Current Intangibles Analysts Firms RD Ownership)

* Determine control variables
global CONTROLS D_length Sentiment Volatility Spread Beta IndVolatility ShrTurn ROE DtA Current Intangibles BtM RD Analysts Firms LateFiler SRC ICW Big4

* Winsorize 1-99
winsor2 *IndDisc DVolatility* DSpread* Volatility* Spread* logMC logTA IndVol RFLength DSHRTURN Fwrd_ivol $CONTROLS ActEst* EPSEst*, replace

* Absolute values
gen DVolatility_abs = abs(DVolatility)
gen DSpread_abs = abs(DSpread)

gen ActEst_abs = abs(ActEst)
gen ActEst_before_abs = abs(ActEst_before)

// gen DActEst = (ActEst_abs - ActEst_before_abs)*100/ActEst_before_abs
// gen DEPSEst = (EPSEst - EPSEst_before)*100/EPSEst_before

bysort Topic_H: egen stdIndDisc = std(IndDisc)
bysort Topic_H: egen stdOtherIndDisc = std(OtherIndDisc)


sort IndDisc
egen quartile = cut( IndDisc ), group(4)

// tabstat discupdate, by(repeated) statistics(n mean sd min p10 p50 p90 max ) columns(statistics)


/*

	***** Main analysis *****

	
*/


quietly{
	reghdfe DVolatility Added Repeated Removed IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M11
	
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M12
	
	reghdfe DSpread Added Repeated Removed IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M13
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M14
} 

estimates table M1*, star(.1, .05, .01) stats(N r2_a F)

esttab M1* using Empirics\results2_individualRFs3.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 
esttab M1* using Empirics\results2_individualRFs3.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 


/* Risk topics specific and not specific to the industry */

quietly{
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if IndSpecific==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M21
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if IndSpecific==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M22
	
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if IndSpecific==0, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M23
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if IndSpecific==0, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store M24
}

estimates table M2*, star(.1, .05, .01) stats(N r2_a)

esttab M2* using Empirics\results2_indSpecificRFs.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 
esttab M2* using Empirics\results2_indSpecificRFs.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 


/*

	***** Additional analysis and robustness*****

	
*/

/* Disclosure in other industries */

quietly{
	reghdfe DVolatility Added Repeated Removed stdIndDisc stdOtherIndDisc c.Added#c.stdIndDisc c.Added#c.stdOtherIndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store M31
	
	reghdfe DSpread Added Repeated Removed stdIndDisc stdOtherIndDisc c.Added#c.stdIndDisc c.Added#c.stdOtherIndDisc  $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store M32
}

estimates table M3*, star(.1, .05, .01) stats(N r2_a)

esttab M3* using Empirics\results2_otherinddisc.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 
esttab M3* using Empirics\results2_otherinddisc.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 


* Covid and financial crisis
quietly{
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if covid==0 & crisis==0, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store R11
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if covid==0 & crisis==0, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store R12
	
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if covid==1 | crisis==1, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store R13
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if covid==1 | crisis==1, absorb(fyear Topic_H CIK) vce(cluster CIK) keepsingletons
	est store R14
}

estimates table R1*, star(.1, .05, .01) stats(N r2_a)

esttab R1* using Empirics\results2_CovidCrisis4.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 
esttab R1* using Empirics\results2_CovidCrisis4.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N) sfmt(%6.3f) 


quietly{
	reghdfe Volatility60 Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R21
	
	reghdfe Spread60 Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R22
	
	reghdfe Fwrd_ivol Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R23
	
	reghdfe ActEst Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc ActEst_before $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R24
}

estimates table R2*, star(.1, .05, .01) stats(N r2_a p)

esttab R2* using Empirics\results2_Robust1.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 
esttab R2* using Empirics\results2_Robust1.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 


/* New RF if never disclosed before */

gen New2 = 0
replace New2 = 1 if Disclosed==1 & DiscSum==1

gen Repeated2 = 0
replace Repeated2 = 1 if Disclosed==1 & DiscSum>1

quietly{
	reghdfe DVolatility New2 Repeated2 Removed IndDisc c.New2#c.IndDisc c.Repeated2#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R31
	
	reghdfe DSpread New2 Repeated2 Removed IndDisc c.New2#c.IndDisc c.Repeated2#c.IndDisc c.Removed#c.IndDisc $CONTROLS, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R32
} 

estimates table R3*, drop($CONTROLS) star(.1, .05, .01) stats(N r2_a F)

esttab R3* using Empirics\results2_Robust2.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 
esttab R3* using Empirics\results2_Robust2.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 


/* RF tone */

gen POS=0
replace POS=1 if Disclosed ==1 & Sentiment >0.1
gen NEG=0
replace NEG=1 if Disclosed ==1 & Sentiment<-0.1

global CONTROLS2 D_length Volatility Spread Beta IndVolatility ShrTurn ROE DtA Current Intangibles BtM RD Analysts Firms LateFiler SRC ICW Big4

quietly{
	reghdfe DVolatility c.Added##c.IndDisc $CONTROLS2 if POS==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R41

	reghdfe DSpread c.Added##c.IndDisc $CONTROLS2 if POS==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R42
	
	reghdfe DVolatility c.Added##c.IndDisc $CONTROLS2 if NEG==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R43

	reghdfe DSpread c.Added##c.IndDisc $CONTROLS2 if NEG==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R44
} 

estimates table R4*, star(.1, .05, .01) stats(N r2_a F)

/*Internal Control*/

global CONTROLS3 D_length Sentiment Volatility Spread Beta IndVolatility ShrTurn ROE DtA Current Intangibles BtM RD Analysts Firms LateFiler SRC

gen GoodIC = 0
replace GoodIC =1 if ICW<=1 & Big4==1

quietly{
	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if GoodIC==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R51

	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if GoodIC==1, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R52

	reghdfe DVolatility Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if GoodIC==0, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R53
	
	reghdfe DSpread Added Repeated Removed IndDisc c.Added#c.IndDisc c.Repeated#c.IndDisc c.Removed#c.IndDisc $CONTROLS if GoodIC==0, absorb(fyear Topic_H CIK) vce(cluster CIK)
	est store R54
}

estimates table R5*, star(.1, .05, .01) stats(N r2_a F)

/*
Likeloohood of disclosure of RFs with respect to the 
*/

global CONTROLS2 Volatility Spread Beta IndVolatility ShrTurn ROE DtA Current Intangibles BtM RD Analysts Firms LateFiler SRC ICW Big4

quietly{
	logistic Disclosed stdIndDisc stdOtherIndDisc IndSpecific LstYrDisc $CONTROLS2 i.CIK i.Topic_H i.fyear, vce(cluster CIK) coef
	est store M41

	logistic Added stdIndDisc stdOtherIndDisc IndSpecific $CONTROLS2 i.CIK i.Topic_H i.fyear if LstYrDisc==0, vce(cluster CIK) coef
	est store M42

	logistic Removed stdIndDisc stdOtherIndDisc IndSpecific $CONTROLS2 i.CIK i.Topic_H i.fyear if LstYrDisc==1, vce(cluster CIK) coef
	est store M43	
}

estimates table M4*, drop(i.CIK i.Topic_H i.fyear) star(.1, .05, .01) stats(N r2_p)

esttab M4* using Empirics\results2_lklhood3.rtf, nogaps drop(*CIK *Topic_H *fyear) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(N r2_p) sfmt(%6.3f) 
esttab M4* using Empirics\results2_lklhood3.tex, drop(*CIK *Topic_H *fyear) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) scalars(N r2_p) sfmt(%6.3f) 

