clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
// import delimited "Data\stats_data_T2V_H.csv" // log_returns
import delimited "Data\stats_data_T2V_H_V2.csv" // 1-year industry average
// import delimited "Data\stats_data_T2V_H_V3.csv" // 6-month industry average

log using Empirics\Study1_T2V.log, replace


* Create variables
gen log_added = log(1+added)
gen log_removed = log(1+removed)
gen log_repeated = log(1+repeated)
gen log_total = log(1+reported_crnt)

gen rel_added = added / reported_crnt
gen rel_removed = removed / reported_last
gen rel_repeated = repeated / reported_crnt

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

replace avg_removed_ind = -1*avg_removed_ind // avg_removed_ind should be positive

* Control for US financial crisis 2007-2009
gen crisis = 0
replace crisis = 1 if inlist(ryear, 2007, 2008, 2009)

* Control for COVID-19 2020-
gen covid = 0
replace covid = 1 if inlist(ryear, 2020, 2021, 2022)

* Generate dependent variables
gen D_std20 = (stdreturn20 - stdreturn_20)/stdreturn_20
gen D_std30 = (stdreturn30 - stdreturn_30)/stdreturn_30

gen D_ba20 = (avgba20 - avgba_20)/avgba_20
gen D_ba30 = (avgba30 - avgba_30)/avgba_30


winsor2 rprt_length reported* repeated* added* removed* rfgap stdreturn* beta* avg* car* D_* log_* shrturn numberofanalysts dta dtebitda roe npm mkvalt logmc at logta rtint intta current tobinq btm rdxopr proprietarycost dearnings, replace


* Determine control variables
global CONTROLS shrturn npm dta current intta btm numberofanalysts dearnings beta_90 late_filer rprt_length //reported_crnt

* Descriptive statistics of variables (after winsorizing)
sum log_repeated log_added log_removed avg_*ind stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS

// drop if missing(shrturn, npm, dta, current, intta, btm, numberofanalysts, dearnings, beta_90, rprt_length)
// logout, save("Empirics\summary.tex") tex replace: sum log_repeated log_added log_removed avg_*ind stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS

* Correlation matrix
pwcorr log_repeated log_added log_removed stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS, star(.01)

// tabstat log_added log_removed stdreturn*20 avgba*20 car*20 D_*20 $CONTROLS, by(ryear) statistics(count, mean)


* Definition of panel and model setup
xtset cik ryear
xtdescribe

* Interaction term
gen interaction1 = log_repeated * avg_repeated_ind
gen interaction2 = log_added * avg_added_ind
gen interaction3 = log_removed * avg_removed_ind

gen interaction12 = rel_repeated * avg_repeated_ind
gen interaction22 = rel_added * avg_added_ind
gen interaction32 = rel_removed * avg_removed_ind

/*

	***** Added Risk Factors *****
	
*/

/* 20-day stock return volatility */
xtreg stdreturn20 log_added $CONTROLS stdreturn_20 i.ryear, fe
est store add_STD

xtreg stdreturn20 log_added avg_added_ind interaction2 $CONTROLS stdreturn_20 i.ryear, fe
est store add_STDi

/* Change 20-day stock return volatility */
xtreg D_std20 log_added $CONTROLS i.ryear, fe
est store add_DSTD

xtreg D_std20 log_added avg_added_ind interaction2 $CONTROLS i.ryear, fe
est store add_DSTDi


/* 20-day average bid-ask spread */
xtreg avgba20 log_added $CONTROLS avgba_20 i.ryear, fe
est store add_BA

xtreg avgba20 log_added avg_added_ind interaction2 $CONTROLS avgba_20 i.ryear, fe
est store add_BAi

/* Change 20-day average bid-ask spread */
xtreg D_ba20 log_added $CONTROLS i.ryear, fe
est store add_DBA

xtreg D_ba20 log_added avg_added_ind interaction2 $CONTROLS i.ryear, fe
est store add_DBAi


/* CAR [-5, +20] */
xtreg car_20 log_added $CONTROLS i.ryear, fe
est store add_CAR

xtreg car_20 log_added avg_added_ind interaction2 $CONTROLS i.ryear, fe
est store add_CARi


* Export all estimation results to Excel
estimates table add*, drop(i.ryear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H2_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab add* using Empirics\results_H2_Final.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 
esttab add* using Empirics\results_H2_Final.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 



/*

	***** Repeated Risk Factors *****
	
*/

/* 20-day stock return volatility */
xtreg stdreturn20 log_repeated $CONTROLS stdreturn_20 i.ryear, fe
est store repeat_STD

xtreg stdreturn20 log_repeated avg_repeated_ind interaction1 $CONTROLS stdreturn_20 i.ryear, fe
est store repeat_STDi


/* Change 20-day stock return volatility */
xtreg D_std20 log_repeated $CONTROLS i.ryear, fe
est store repeat_DSTD

xtreg D_std20 log_repeated avg_repeated_ind interaction1 $CONTROLS i.ryear, fe
est store repeat_DSTDi


/* 20-day average bid-ask spread */
xtreg avgba20 log_repeated $CONTROLS avgba_20 i.ryear, fe
est store repeat_BA

xtreg avgba20 log_repeated avg_repeated_ind interaction1 $CONTROLS avgba_20 i.ryear, fe
est store repeat_BAi


/* Change 20-day average bid-ask spread */
xtreg D_ba20 log_repeated $CONTROLS i.ryear, fe
est store repeat_DBA

xtreg D_ba20 log_repeated avg_repeated_ind interaction1 $CONTROLS i.ryear, fe
est store repeat_DBAi


/* CAR [-5, +20] */
xtreg car_20 log_repeated $CONTROLS i.ryear, fe
est store repeat_CAR

xtreg car_20 log_repeated avg_repeated_ind interaction1 $CONTROLS i.ryear, fe
est store repeat_CARi


* Export all estimation results to Excel
estimates table repeat*, drop(i.ryear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H1_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab repeat* using Empirics\results_H1_Final.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 
esttab repeat* using Empirics\results_H1_Final.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 



/*

	***** Removed Risk Factors *****
	
*/

/* 20-day stock return volatility */
xtreg stdreturn20 log_removed $CONTROLS stdreturn_20 i.ryear, fe
est store remove_STD

xtreg stdreturn20 log_removed avg_removed_ind interaction3 $CONTROLS stdreturn_20 i.ryear, fe
est store remove_STDi


/* Change 20-day stock return volatility */
xtreg D_std20 log_removed $CONTROLS i.ryear, fe
est store remove_DSTD

xtreg D_std20 log_removed avg_removed_ind interaction3 $CONTROLS i.ryear, fe
est store remove_DSTDi


/* 20-day average bid-ask spread */
xtreg avgba20 log_removed $CONTROLS avgba_20 i.ryear, fe
est store remove_BA

xtreg avgba20 log_removed avg_removed_ind interaction3 $CONTROLS avgba_20 i.ryear, fe
est store remove_BAi

/* Change 20-day average bid-ask spread */
xtreg D_ba20 log_removed $CONTROLS i.ryear, fe
est store remove_DBA

xtreg D_ba20 log_removed avg_removed_ind interaction3 $CONTROLS i.ryear, fe
est store remove_DBAi


/* CAR [-5, +20] */
xtreg car_20 log_removed $CONTROLS i.ryear, fe
est store remove_CAR

xtreg car_20 log_removed avg_removed_ind interaction3 $CONTROLS i.ryear, fe
est store remove_CARi


* Export all estimation results to Excel
estimates table remove*, drop(i.ryear) star(.1, .05, .01) stats(N r2_a p)

* Set the excel file to export the regression results
putexcel set "Empirics\reg_results.xlsx", modify sheet(H3_Final, replace)
putexcel (A1) = etable

* Estimation results to word document
esttab remove* using Empirics\results_H3_Final.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 
esttab remove* using Empirics\results_H3_Final.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) r2 ar2 scalars(p_f ll) sfmt(%6.3f) 


* Additional analysis
xtreg D_std20 avg_added $CONTROLS i.ryear, fe

xtreg D_ba20 avg_added $CONTROLS i.ryear, fe

xtreg car_20 avg_added $CONTROLS i.ryear, fe

/* Firms tend to repeat what they have discussed in previouse risk reports because this signals that things are under control, but they are reluctant of adding new risk factors as this is signal of higher uncertainty. Therefore, they tend to postpone their disclosures if sth is wrong */
xtreg rfgap log_added shrturn npm dta current intta btm numberofanalysts dearnings beta_90 rprt_length i.ryear, fe
xtreg rfgap log_repeated shrturn npm dta current intta btm numberofanalysts dearnings beta_90 rprt_length i.ryear, fe

log close