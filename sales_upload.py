# Python 3.4.3 (v3.4.3:9b73f1c3e601, Feb 23 2015, 02:52:03)
# [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
################################################################################
#
# Description: This program handles the preprocessing of the reports needed to
#   track company sales and sales rep productivity/ commission
#
# Written By: Matthew Stadelman
# Date Written: 2016/06/12
#
# Modified By: Matthew Stadelman
# Last Modifed: 2016/06/12
#
################################################################################
#
import sales_parsing
#

ar_sales_list = []
customer_ar_dict = {}
rep_totals_dict = {}
## need to create a log to handle all errors and then have that emailed to justin
#
# finding the reqired files
file_dict = get_filenames()
#
# setting file names
ec_infile = 'EC-Order-Upload.txt'
sales_infile = file_dict['ar_sales']
ar_infile = file_dict['ar_ovchs']
com_infile = file_dict['s_wkcomm']
#
# processing the EC upload file
sold_items_list = read_ec_order_upload(ec_infile)
#
# processing the ar_sales file
process_ar_sales_file(sales_infile,rep_totals_dict)
#
# processing the ar_ovchs file
process_ar_ovchs_file(ar_infile,rep_totals_dict)
#
# processing the s_wkcomm file
process_s_wkcomm_file(com_infile,rep_totals_dict)
#
# creating sql upload statments
sales_dict_list = make_sales_sql_dicts(sold_items_list)
rep_dict_list  = make_rep_sql_dicts(rep_totals_dict)
#
sales_sql  = create_sql('sales_data',sales_dict_list)
rep_sql  = create_sql('sales_rep_data',rep_dict_list)
#
# outputting the sql commands
with open('sales-upload.sql','w') as sql_file:
    sql_file.write(rep_sql)
    sql_file.write('\n')
    sql_file.write(sales_sql)
    sql_file.close()



sold_items_list = read_ec_order_upload(ec_infile)
sales_dict_list = make_sales_sql_dicts(sold_items_list)
rep_sql = ''
sales_sql  = create_sql('sales_data',sales_dict_list)
with open('sales-upload-2016.sql','w') as sql_file:
    sql_file.write(sales_sql)
    sql_file.close()