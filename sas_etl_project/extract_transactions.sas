/* Extract Transactions */
/* Simulating data extraction from an external source into a staging dataset */

data staging.raw_transactions;
    length transaction_id $10 region $2 product $20;
    input transaction_id $ region $ amount product $ date : yymmdd10.;
    format date yymmdd10.;
    datalines;
T001 NA 100.00 WidgetA 2023-01-01
T002 EU 200.00 WidgetB 2023-01-01
T003 AS 150.00 WidgetA 2023-01-02
T004 NA 120.00 WidgetC 2023-01-02
T005 EU 250.00 WidgetB 2023-01-03
;
run;

proc sort data=staging.raw_transactions;
    by transaction_id;
run;

