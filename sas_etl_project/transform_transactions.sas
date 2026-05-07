/* Transform Transactions */
/* Cleans data and calculates derived fields */

/* Ensure macros are available */
%include "common_setup.sas";

data staging.clean_transactions;
    set staging.raw_transactions;
    
    /* Apply string cleaning */
    %clean_string(product);
    %clean_string(region);
    
    /* Calculate Tax */
    %calc_tax(amount, region);
    
    total_amount = amount + tax;
    
    /* Flag high value transactions */
    if total_amount > 200 then high_value_flag = 1;
    else high_value_flag = 0;
    
    label total_amount = "Total Amount including Tax";
run;

/* Validation step */
proc freq data=staging.clean_transactions;
    tables region high_value_flag;
run;

