clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
// import delimited "Data\stats_data_T2V_H.csv" // log_returns
// import delimited "Data\stats_data_T2V_H_V2.csv" // 1-year industry average
import delimited "Data\stats_data_T2V_H_V3.csv" // non disclosure
// import delimited "Data\stats_data_T2V_H_V4.csv" // T2V with 85 topics


log using Empirics\Study1_T2V.log, replace


* Create variables
gen log_added = log(1+added)
gen log_removed = log(1+removed)
gen log_repeated = log(1+repeated)
gen log_total = log(1+reported_crnt)

gen rel_added = added / reported_crnt
gen rel_removed = removed / reported_last
gen rel_repeated = repeated / reported_last

egen stdadd = std(added)
egen stdrepeat = std(repeated)
egen stdremove = std(removed)

encode industry, generate(industry_cat)

gen SRC = category=="SRC"


/* Form 10-K is due within 60 days for Large Accelerated filers, within 75 days for Accelerated Filers, and within 90 days for Non-Accelerated Filers after the end of the fiscal year. An NT-10K may be filed up to 24 hours after the 10-K due date to recieve a 15-day extension on Form 10-K. */
gen late_filer = 0
replace late_filer = 1 if rfgap >= 75


* Scale up dependent variables
foreach v of varlist stdreturn* {
    replace `v' = `v'*100
  } 

foreach v of varlist avgba* {
    replace `v' = `v'*100
  } 

foreach v of varlist car* {
    replace `v' = `v'*100
  } 

replace at = at/1000 // to billion
replace mkvalt = mkvalt/1000

replace shrturn = shrturn*100

replace avg_removed_ind = -1*avg_removed_ind // avg_removed_ind should be positive

* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if inlist(fyear, 2007, 2008, 2009)

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if inlist(fyear, 2020, 2021, 2022)

* Generate dependent variables
gen D_std20 = (stdreturn20 - stdreturn_20)*100/stdreturn_20
gen D_std30 = (stdreturn30 - stdreturn_30)*100/stdreturn_30

gen D_ba20 = (avgba20 - avgba_20)*100/avgba_20
gen D_ba30 = (avgba30 - avgba_30)*100/avgba_30


drop if missing(shrturn, npm, dta, current, intta, btm, numberofanalysts, dearnings, beta_90, rprt_length)

winsor2 rel_* std* rprt_length reported* repeated* added* removed* rfgap beta* avg* car* D_* log_* shrturn numberofanalysts dta dtebitda roe npm mkvalt logmc at logta rtint intta current tobinq btm rdxopr proprietarycost dearnings, replace


* Determine control variables
global CONTROLS shrturn npm dta current intta btm numberofanalysts dearnings beta_90 late_filer stdreturn_20 avgba_20 //rprt_length //reported_crnt

* Descriptive statistics of variables (after winsorizing)
sum log_* avg_*ind stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS

// logout, save("Empirics\summary.tex") tex replace: tabstat reported* repeated* added* removed* avg_*ind stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS, statistics(mean sd p25 p50 p75) columns(statistics) format(%9.3f)

// logout, save("Empirics\year_mean.tex") tex replace: tabstat reported_crnt repeated added removed avg_repeated_ind avg_added_ind avg_removed_ind, by(fyear) format(%6.2f)

* Correlation matrix
pwcorr log_* stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS, star(.01)

* Definition of panel and model setup
xtset cik


/*

	***** Added Risk Factors *****
	
*/

/* 20-day stock return volatility */
xtreg stdreturn20 log_added avg_added_ind $CONTROLS stdreturn_20 i.fyear, fe
est store add_STD

xtreg stdreturn20 c.log_added##c.avg_added_ind $CONTROLS stdreturn_20 i.fyear, fe
est store add_STDi

/* Change 20-day stock return volatility */
xtreg D_std20 log_added avg_added_ind $CONTROLS i.fyear, fe
est store add_DSTD

xtreg D_std20 c.log_added##c.avg_added_ind $CONTROLS i.fyear, fe
est store add_DSTDi

/* CAR [-5, +20] */
xtreg car_20 log_added avg_added_ind $CONTROLS i.fyear, fe
est store add_CAR

xtreg car_20 c.log_added##c.avg_added_ind $CONTROLS i.fyear, fe
est store add_CARi

/* 20-day average bid-ask spread */
xtreg avgba20 log_added avg_added_ind $CONTROLS avgba_20 i.fyear, fe
est store add_BA

xtreg avgba20 c.log_added##c.avg_added_ind $CONTROLS avgba_20 i.fyear, fe
est store add_BAi

/* Change 20-day average bid-ask spread */
xtreg D_ba20 log_added avg_added_ind $CONTROLS i.fyear, fe
est store add_DBA

xtreg D_ba20 c.log_added##c.avg_added_ind $CONTROLS i.fyear, fe
est store add_DBAi


* Export all estimation results to Excel
estimates table add*, drop(i.fyear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H2_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab add* using Empirics\results_AddedRFs.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 
esttab add* using Empirics\results_AddedRFs.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 



/*

	***** Repeated Risk Factors *****
	
*/

/* 20-day stock return volatility */
xtreg stdreturn20 log_repeated avg_repeated_ind $CONTROLS stdreturn_20 i.fyear, fe
est store repeat_STD

xtreg stdreturn20 c.log_repeated##c.avg_repeated_ind $CONTROLS stdreturn_20 i.fyear, fe
est store repeat_STDi


/* Change 20-day stock return volatility */
xtreg D_std20 log_repeated avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_DSTD

xtreg D_std20 c.log_repeated##c.avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_DSTDi


/* CAR [-5, +20] */
xtreg car_20 log_repeated avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_CAR

xtreg car_20 c.log_repeated##c.avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_CARi


/* 20-day average bid-ask spread */
xtreg avgba20 log_repeated avg_repeated_ind $CONTROLS avgba_20 i.fyear, fe
est store repeat_BA

xtreg avgba20 c.log_repeated##c.avg_repeated_ind $CONTROLS avgba_20 i.fyear, fe
est store repeat_BAi


/* Change 20-day average bid-ask spread */
xtreg D_ba20 log_repeated avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_DBA

xtreg D_ba20 c.log_repeated##c.avg_repeated_ind $CONTROLS i.fyear, fe
est store repeat_DBAi



* Export all estimation results to Excel
estimates table repeat*, drop(i.fyear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H1_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab repeat* using Empirics\results_RepeatedRFs.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 
esttab repeat* using Empirics\results_RepeatedRFs.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 



/*

	***** All Risk Factors *****
	
*/


/* 20-day stock return volatility */
xtreg stdreturn20 stdadd stdrepeat stdremove avg_all_ind avg_removed_ind $CONTROLS i.fyear, fe
est store all_STD

xtreg stdreturn20 c.stdadd##c.avg_all_ind stdrepeat c.stdrepeat#c.avg_all_ind c.stdremove##c.avg_removed_ind $CONTROLS i.fyear, fe
est store all_STDi

/* Change 20-day stock return volatility */
xtreg D_std20 stdadd stdrepeat stdremove avg_all_ind avg_removed_ind $CONTROLS i.fyear, fe
est store all_DSTD

xtreg D_std20 c.stdadd##c.avg_all_ind stdrepeat c.stdrepeat#c.avg_all_ind c.stdremove##c.avg_removed_ind $CONTROLS i.fyear, fe
est store all_DSTDi


/* CAR [-5, +20] */
xtreg car_20 stdadd stdrepeat stdremove avg_all_ind avg_removed_ind $CONTROLS i.fyear, fe
est store all_CAR

xtreg car_20 c.stdadd##c.avg_all_ind stdrepeat c.stdrepeat#c.avg_all_ind c.stdremove##c.avg_removed_ind $CONTROLS i.fyear, fe
est store all_CARi


/* 20-day average bid-ask spread */
xtreg avgba20 stdadd stdrepeat stdremove avg_all_ind avg_removed_ind $CONTROLS i.fyear, fe
est store all_BA

xtreg avgba20 c.stdadd##c.avg_all_ind stdrepeat c.stdrepeat#c.avg_all_ind c.stdremove##c.avg_removed_ind $CONTROLS i.fyear, fe
est store all_BAi

/* Change 20-day average bid-ask spread */
xtreg D_ba20 stdadd stdrepeat stdremove avg_all_ind avg_removed_ind $CONTROLS i.fyear, fe
est store all_DBA

xtreg D_ba20 c.stdadd##c.avg_all_ind stdrepeat c.stdrepeat#c.avg_all_ind c.stdremove##c.avg_removed_ind $CONTROLS i.fyear, fe
est store all_DBAi



* Export all estimation results to Excel
estimates table all*, drop(i.fyear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H2_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab remov* using Empirics\results_RemovedRFs.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 
esttab remov* using Empirics\results_RemovedRFs.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 



* Additional analysis
xtreg D_std20 avg_added $CONTROLS i.fyear, fe

xtreg D_ba20 avg_added $CONTROLS i.fyear, fe

xtreg car_20 avg_added $CONTROLS i.fyear, fe

/* Firms tend to repeat what they have discussed in previouse risk reports because this signals that things are under control, but they are reluctant of adding new risk factors as this is signal of higher uncertainty. Therefore, they tend to postpone their disclosures if sth is wrong */
xtreg rfgap log_added shrturn npm dta current intta btm numberofanalysts dearnings beta_90 rprt_length i.fyear, fe
xtreg rfgap log_repeated shrturn npm dta current intta btm numberofanalysts dearnings beta_90 rprt_length i.fyear, fe

log close