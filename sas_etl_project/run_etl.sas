/* Master ETL Job */
/* Orchestrates the ETL process */

/* 1. Setup environment */
%include "common_setup.sas";

/* 2. Extract Data */
%include "extract_transactions.sas";

/* 3. Transform Data */
/* Note: transform_transactions also includes common_setup, which is fine */
%include "transform_transactions.sas";

/* 4. Load Data */
%include "load_daily_summary.sas";

/* 5. Final Reporting */
proc print data=mart.daily_sales;
    where grand_total > 0;
    title "Final ETL Report";
run;

%put ETL Process Completed Successfully;

