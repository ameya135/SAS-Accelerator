/* Simple SAS Example for Testing Graph Builder */

/* Define a macro variable */
%LET year = 2024;

/* Macro definition */
%MACRO calculate_bonus(dept);
    DATA &dept._bonus;
        SET employee_data;
        WHERE department = "&dept";
        bonus = salary * 0.10;
    RUN;
%MEND calculate_bonus;

/* Read raw data */
DATA employee_data;
    INPUT emp_id name $ department $ salary;
    DATALINES;
1 John Sales 50000
2 Jane IT 60000
3 Bob HR 55000
;
RUN;

/* Filter high performers */
DATA high_performers;
    SET employee_data;
    WHERE salary > 55000;
RUN;

/* Calculate statistics */
PROC MEANS DATA=high_performers;
    VAR salary;
    OUTPUT OUT=salary_stats MEAN=avg_salary STD=std_salary;
RUN;

/* Call the macro */
%calculate_bonus(Sales);

/* Print results */
PROC PRINT DATA=salary_stats;
RUN;
