/* Load Daily Summary */
/* Aggregates transaction data into a daily summary mart */

/* explicit dependency on previous step's output */
data work.input_data;
    set staging.clean_transactions;
run;

proc summary data=work.input_data nway;
    class date region product;
    var amount tax total_amount;
    output out=mart.daily_sales (drop=_type_ _freq_)
        sum(amount)=total_sales
        sum(tax)=total_tax
        sum(total_amount)=grand_total;
run;

/* Append to historical table if it exists (simulated) */
/* 
proc append base=mart.history_sales data=mart.daily_sales force;
run;
*/

proc print data=mart.daily_sales;
    title "Daily Sales Summary";
run;

