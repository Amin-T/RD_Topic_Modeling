clear all
capture log close
set more off

cd "C:\Users\u0147656\Desktop\PyCodes"

* Load data
import delimited "Data\study1_more.csv" // with frac, historical sic and topic_h from topic_hierarchies
// import delimited "Data\study1_more(2)(2).csv" // no. firms in industry with filings_df
// import delimited "Data\study1_more(2).csv"

log using Empirics\Study1_T2V.log, replace


* Create variables

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

replace shrturn = shrturn*100


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


drop if missing(shrturn, npm, dta, current, intta, btm, numberofanalysts, dearnings, beta_90, rprt_length, frac)


* Determine control variables
global CONTROLS shrturn npm dta current intta btm numberofanalysts dearnings beta_90 late_filer rprt_length firms //reported_crnt

winsor2 stdreturn20 stdreturn_20 D_std20 car_20 avgba20 avgba_20 D_ba20 frac $CONTROLS, replace


/* Dummy for occurrence */
// drop if max_occ < 5
local n = 1
while `n' < 6 {
	gen occ_`n' = (occurence == `n')
	local n = `n' + 1
}

xtset, clear
xtset topic

replace frac = frac*100

xtreg stdreturn20 occurence frac $CONTROLS stdreturn_20 i.fyear, fe
est store occ_STD

xtreg stdreturn20 c.occurence##c.frac $CONTROLS stdreturn_20 i.fyear, fe
est store occ_STDi

xtreg D_std20 occurence frac $CONTROLS i.fyear, fe
est store occ_DSTD

xtreg D_std20 c.occurence##c.frac $CONTROLS i.fyear, fe
est store occ_DSTDi

gen CAR = abs(car_20)
xtreg CAR occurence frac $CONTROLS i.fyear, fe
est store occ_CAR

xtreg CAR c.occurence##c.frac $CONTROLS i.fyear, fe
est store occ_CARi

xtreg D_ba20 occurence frac $CONTROLS i.fyear, fe
est store occ_DBA

xtreg D_ba20 c.occurence##c.frac $CONTROLS i.fyear, fe
est store occ_DBAi

* Export all estimation results to Excel
estimates table occ*, drop(i.fyear) star(.1, .05, .01) stats(N r2_a p)

* Plot coefs
margins, dydx(occ*) post
marginsplot


* Estimation results to word document
esttab occ* using Empirics\results_Occurence.rtf, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 
esttab occ* using Empirics\results_Occurence.tex, star(* 0.1 ** 0.05 *** 0.01) b(%6.5f) ar2 scalars(p_f) sfmt(%6.3f) 


*Calculate marginal effects at different values for frac and occurence4 holding all other variables at the mean values (atmeans)
xtreg stdreturn20 c.occurence##c.frac $CONTROLS stdreturn_20 i.fyear, fe
margins, at(frac=(0(0.1)1) occurence=(1(1)5)) vsquish atmeans
marginsplot ///
		, /// after the comma you can specific numerous options (see the following code lines)
		title("", color(black)) /// remove default title from figure (insert your own title between "")
		x(frac) /// define x-axis
		xtitle({bf:% Disclosing firms}) /// label on x-axis (bf stands for bold fond)
		ytitle("{bf:Average of Volatility}") /// label on y-axis (bf stands for bold fond and the two parentheses break the label into two lines)
		ylabel(, grid glcolor(gs15) angle(hor) labcol(black) format(%10.1fc)) /// set color of horizontal grid lines (greyscale 15), set angle of y-labels (horizontal), set color of y-label (black), set number of decimal places for y-label (1; use 10.2 for two decimal places)
		recast(line) recastci(rcap) /// set appearance of confidence intervals
		ci1op(color(forest_green%50)) ci2op(color(purple%50)) /// set color and level of transparency of confidence intervals
		plotregion(col(white)) graphregion(color(white)) bgcolor(white) /// set color of figure background
		plot1opts(msym(S)mcol(black)lpattern(solid)) /// appearance of first line 
		plot2opts(msym(S)mcol(black)lpattern(shortdash)) /// appearance of second line 
		plot3opts(msym(S)mcol(black)lpattern(dash))
		legend(order(1 "Occurrence=1" 2 "Occurrence=2" 3 "Occurrence=3" 4 "Occurrence=4" 5 "Occurrence=5") cols(2)) // label in legends and number of columns for legend

graph export "Margins_Child_1.tif", replace width(1920) height(1080)


/* Dummy for fraction of industry */
drop if max_frac < 0.5
local n = 1
while `n' < 6 {
	gen frac_`n' = (frac >= (`n'-1)*0.2 & frac < `n'*0.2)
	local n = `n' + 1
}

xtset, clear
xtset topic

xtreg stdreturn20 frac_* $CONTROLS firms stdreturn_20 i.fyear, fe
est store frac_STD

xtreg D_std20 frac_* $CONTROLS firms i.fyear, fe
est store frac_DSTD

xtreg car_20 frac_* $CONTROLS firms i.fyear, fe
est store frac_CAR

xtreg avgba20 frac_* $CONTROLS firms i.fyear avgba_20, fe
est store frac_BA

xtreg D_ba20 frac_* $CONTROLS firms i.fyear, fe
est store frac_DBA

* Export all estimation results to Excel
estimates table frac*, drop(i.fyear) star(.1, .05, .01) stats(N r2_a p)

* Plot coefs
margins, dydx(frac_*) post
marginsplot //, yscale(reverse)


graph combine "Empirics\Dvol_firm.gph" "Empirics\Dvol_ind.gph"

log close