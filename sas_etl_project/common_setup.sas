/* Common Setup: Libraries and Macros */

libname mart 'data/mart';
libname staging 'data/staging';

options mprint symbolgen;

/* Macro to calculate tax based on region */
%macro calc_tax(amount, region);
    %if &region = 'NA' %then %do;
        tax = &amount * 0.10;
    %end;
    %else %if &region = 'EU' %then %do;
        tax = &amount * 0.20;
    %end;
    %else %do;
        tax = &amount * 0.05;
    %end;
%mend calc_tax;

/* Macro to clean string fields */
%macro clean_string(field);
    &field = upcase(strip(&field));
%mend clean_string;

