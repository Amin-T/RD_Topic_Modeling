clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\Study1_data1_V3.csv", case(preserve) 

* Create variables

// How many risk factors are added, repeated, or removed compared to the last year's report
gen rel_added = (added / reported_crnt)*100 // % of new risk factors in the currecnt years report
gen rel_repeated = (repeated / reported_last)*100 // % of risk factors repeated from last year

gen TotalRFs = log(reported_crnt+1)
gen New = log(added+1)
gen Repeated = log(repeated+1)

replace removed = -1*removed 
gen Removed = log(removed+1)


gen DeltaRFLength = Delta_length/1000
gen RRLength = rprt_length / 1000


* SRC with Free Float less than $75 million (Cheng, 2013)
replace FREEFLOAT = FREEFLOAT/1000000
gen SRC = 0
replace SRC = 1 if FREEFLOAT < 75


/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen LateFiler = 0
replace LateFiler = 1 if rfGap >= 75

* Scale up dependent variables
foreach v of varlist Volatility* Spread* CAR*{
    replace `v' = `v'*100
  } 
  
foreach v of varlist IndAdded IndRepeated IndRemoved IndDisc OtherIndAdded OtherIndDisc {
    replace `v' = `v'*100
  } 

replace SHRTURN = SHRTURN*100
replace IndRemoved = -1*IndRemoved // IndRemoved should be positive


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

// * Replace IndDisc variables with 0
// replace IndAdded=0 if added==0
// replace IndRepeated=0 if repeated==0
// replace IndRemoved=0 if removed==0

* Missing variables
drop if missing(New, Removed, IndAdded, IndRemoved, DVolatility, DSpread, SHRTURN, ROE, DtA, current, INTtA, BtM, NUMBEROFANALYSTS, Beta_120, Volatility_120, Spread_120, firms, LateFile, IndDisc, IndVol_, RDxopr, SRC) //CategoryPercentOfTradedShares


replace COUNT_WEAK=0 if missing(COUNT_WEAK)
replace Big4=0 if missing(Big4)

* Drop firms with only one observations
bysort CIK: egen long cnt_obs = count(fyear)
drop if cnt_obs < 2


// Standardize raw numbers --> to be used if all in one model
bysort FF: egen stdtotal = std(reported_crnt)
bysort FF: egen stdadd = std(added)
bysort FF: egen stdrepeat = std(repeated)
bysort FF: egen stdremove = std(removed)

bysort FF: egen stdIndAdded = std(IndAdded)
bysort FF: egen stdIndRepeated = std(IndRepeated)
bysort FF: egen stdIndRemoved = std(IndRemoved)

gen ICW = log(COUNT_WEAK+1)

* Rename variables 
rename (Volatility_120 Spread_120 Beta_120 IndVol_ SHRTURN INTtA NUMBEROFANALYSTS firms RDxopr current CategoryPercentOfTradedShares) (Volatility Spread Beta IndVolatility ShrTurn Intangibles Analysts Firms RD Current Ownership)

* Determine control variables
global CONTROLS DeltaRFLength Sentiment Volatility Spread Beta IndVolatility ShrTurn ROE DtA Current Intangibles BtM RD Analysts Firms LateFiler Big4 ICW //FOG Ownership 

winsor2 New Repeated Removed Fwrd_ivol EPSEst* ActEst* TotalRFs *Volatility* *Spread* IndAdded IndRepeated IndRemoved IndDisc $CONTROLS std* rel_* FOG Ownership, replace

* Absolute values
gen DVolatility_abs = abs(DVolatility)
gen DSpread_abs = abs(DSpread)
gen CAR = abs(CAR_5)
gen CAR2 = abs(CAR_2)

gen ActEst_abs = abs(ActEst)
gen ActEst_before_abs = abs(ActEst_before)

gen DActEst = (ActEst_abs - ActEst_before_abs)*100/ActEst_before_abs
gen DEPSEst = (EPSEst - EPSEst_before)*100/EPSEst_before

* Descriptive statistics of variables (after winsorizing)
tabstat reported_crnt added repeated removed IndDisc IndAdded IndRepeated IndRemoved DVolatility DSpread $CONTROLS Fwrd_ivol ActEst, statistics(n mean sd p10 p50 p90) columns(statistics)

// logout, save("Empirics\summary4.tex") tex replace: tabstat reported_crnt added repeated removed IndDisc IndAdded IndRepeated IndRemoved DVolatility DSpread $CONTROLS Fwrd_ivol ActEst, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
// logout, save("Empirics\summary4.rtf") word replace: tabstat reported_crnt added repeated removed IndDisc IndAdded IndRepeated IndRemoved DVolatility DSpread $CONTROLS Fwrd_ivol ActEst, statistics(n mean sd p10 p50 p90) columns(statistics) format(%9.3f)
//
// logout, save("Empirics\pwcorr4.tex") tex replace: pwcorr stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved DVolatility DSpread Volatility30 Spread30, star(.01)



/*

	***** Main analysis *****

	
*/


quietly{
	reghdfe DVolatility stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store M1DVolatility
	
	reghdfe DSpread stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store M1DSpread
	
	reghdfe Volatility30 stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store M1Volatility
	
	reghdfe Spread30 stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store M1Spread
}

estimates table M1*, star(.1, .05, .01) stats(N r2_a F)

esttab M1* using Empirics\results1_NoRFs.rtf, nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 
esttab M1* using Empirics\results1_NoRFs.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 


/*

	***** Additional analysis and robustness*****

	
*/

/*Robustness*/

quietly {
	reghdfe Volatility60 stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store R1Volatility
	
	reghdfe Spread60 stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved $CONTROLS, absorb(CIK fyear) keepsingletons
	est store R1Spread
	
	reghdfe Fwrd_ivol stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved ivol $CONTROLS, absorb(CIK fyear) keepsingletons
	est store R1IVol
	
	reghdfe ActEst stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved ActEst_before $CONTROLS, absorb(CIK fyear) keepsingletons
	est store R1EstError
}

estimates table R1*, star(.1, .05, .01) stats(N r2_a F)


esttab R1* using Empirics\results1_Robust1.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 
esttab R1* using Empirics\results1_Robust1.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 


* COVID-19 and Financial crisis
quietly{
	reghdfe DVolatility stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved crisis c.stdadd#c.crisis c.stdrepeat#c.crisis c.stdremove#c.crisis c.stdIndAdded#c.crisis c.stdIndRepeated#c.crisis c.stdIndRemoved#c.crisis $CONTROLS if ryear<=2019, absorb(CIK fyear) keepsingletons
	est store R2VolCris
	
	reghdfe DSpread stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved crisis c.stdadd#c.crisis c.stdrepeat#c.crisis c.stdremove#c.crisis c.stdIndAdded#c.crisis c.stdIndRepeated#c.crisis c.stdIndRemoved#c.crisis $CONTROLS if ryear<=2019, absorb(CIK fyear) keepsingletons
	est store R2BACris
	
	reghdfe DVolatility stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved covid c.stdadd#c.covid c.stdrepeat#c.covid c.stdremove#c.covid c.stdIndAdded#c.covid c.stdIndRepeated#c.covid c.stdIndRemoved#c.covid $CONTROLS if ryear>=2010, absorb(CIK fyear) keepsingletons
	est store R2VolCov
	
	reghdfe DSpread stdadd stdrepeat stdremove stdIndAdded stdIndRepeated stdIndRemoved covid c.stdadd#c.covid c.stdrepeat#c.covid c.stdremove#c.covid c.stdIndAdded#c.covid c.stdIndRepeated#c.covid c.stdIndRemoved#c.covid $CONTROLS if ryear>=2010, absorb(CIK fyear) keepsingletons
	est store R2BACov
}

estimates table R2*, drop($CONTROLS) star(.1, .05, .01) stats(N r2_a)


esttab R2* using Empirics\results1_CovidCrisis3.rtf, drop($CONTROLS) nogaps star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 
esttab R2* using Empirics\results1_CovidCrisis3.tex, drop($CONTROLS) star(* 0.1 ** 0.05 *** 0.01) b(%6.4f) ar2 scalars(N F) sfmt(%6.3f) 




