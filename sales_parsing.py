# Python 3.4.3 (v3.4.3:9b73f1c3e601, Feb 23 2015, 02:52:03) 
# [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
################################################################################
#
# Description: This program handles the preprocessing of the reports needed to 
#   track company sales and sales rep productivity/ commission
#
# Written By: Matthew Stadelman
# Date Written: 2015/01/18
#
# Modified By: 
# Last Modifed: 
#
################################################################################
#
#
# module imports
import re
import os
#
#
################################################################################
############################## Class Definitions ###############################
################################################################################
#
# stores an individual items information
class sold_item:
    #
    def __init__(self,input_str):
        # initializations (col_names will have something in it once Justin gets back with me)
        self.rep_id = 0
        self.customer_id = 0
        self.date = ''
        self.price = 0.00
        self.cost = 0.00
        self.col_dict = {}
        # processing input string
        col_names = []
        input_arr = re.split(r'\t',input_str)
        for i in range(len(input_arr)):
            col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
            self.col_dict[col] = input_arr[i].strip()
        #
        # updating variables
        self.rep_id = self.col_dict['col-0'].split(' ')[0]  #these will be replaced with useful col names
        self.customer_id = self.col_dict['col-3']
        self.date  = self.col_dict['col-4']
        self.price = float(self.col_dict['col-11'])
        self.cost  = float(self.col_dict['col-14'])        
    #
    def getCol(self,key):
        return(self.col_dict[key])
#
# this stores the line data from the ar_ovchs report
class ar_line:
    #
    def __init__(self,input_str,col_starts):
        # initializations
        self.rep_id = 0
        self.customer_id = 0
        self.date = ''
        self.amount = 0.00
        self.col_dict = {}
        # processing input string
        col_names = ['customer_id','name','desc','address','phone','rep_id','city','state','over','ar_ttl']
        line = ''
        for i in range(len(col_starts)-1):
            col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
            self.col_dict[col] = input_str[col_starts[i]:col_starts[i+1]].strip()
        i += 1
        col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
        self.col_dict[col] = input_str[col_starts[-1]:].strip()
        # updating variables
        self.rep_id = self.col_dict['rep_id']
        self.customer_id = self.col_dict['customer_id']
        # checking for appended negative sign
        if (re.search('-$',self.col_dict['over'])):
            self.col_dict['over'] = '-'+re.sub('-$','',self.col_dict['over'])
        self.amount = float(self.col_dict['over'])
    #
    def getCol(self,key):
        return(self.col_dict[key])
#
# stores customer information and totals 
class customer:
    #
    def __init__(self,customer_id):
        self.id = customer_id
        self.daily_sales = {}
        self.daily_costs = {}
        self.ar_total = {}
    #
    def incrementSales(self,date,price,cost):
        try:
            self.daily_sales[date] += price
            self.daily_costs[date] += cost
        except KeyError:
            self.daily_sales[date]  = price
            self.daily_costs[date]  = cost
#
#
################################################################################
############################ Function Definitions ##############################
################################################################################
#
# ### ### EC Upload File Processing ### ### #
#
#
# this processes the ec upload file and populates the sold_items_list
def read_ec_order_upload(infile,sold_items_list):
    # reading infile
    upload_file = open(infile,'r')
    content = upload_file.read()
    upload_file.close()
    #
    # splitting lines 
    content_arr = re.split(r'\n',content)
    content_arr = list(filter(None,content_arr))
    #
    for i in range(len(content_arr)):
        item = sold_item(content_arr[i])
        sold_items_list.append(item)
#
# this totals each customers sales
def customer_totals(customer_sales_dict,sold_items_list):
    for item in sold_items_list:
        try:
            cust = customer_sales_dict[item.customer_id]
            cust.incrementSales(item.date,item.price,item.cost)
        except KeyError:
            cust = customer(item.customer_id)
            cust.incrementSales(item.date,item.price,item.cost)
            customer_sales_dict[item.customer_id] = cust
#
# this just acts as a driver function to handle all processing of EC upload file
def process_ec_order_upload(ec_infile,sold_items_list,customer_sales_dict):
    #
    # reading EC upload file
    read_ec_order_upload(ec_infile,sold_items_list)
    #
    # totaling customer sales and cost
    customer_totals(customer_sales_dict,sold_items_list)
#
#
# ### ### ar_ovchs File Processing ### ### #
#
#
# this function reads the ar_ovchs file 
def read_ar_ovchs(ar_infile,customer_ar_dict):
    # reading infile
    ar_file = open(ar_infile,'r')
    content = ar_file.read()
    ar_file.close()
    #
    # splitting lines 
    content_arr = re.split(r'\n',content)
    content_arr = list(filter(None,content_arr))
    #
    # getting date from first header
    date = re.split('\s{2,}',content_arr[1])[2]
    date = date.strip()
    #
    # filtering uneeded lines
    i = 0
    max_len = 0
    while i < len(content_arr):
        line = content_arr[i]
        #
        if not (re.match(r'\s{1,6}[A-Z0-9]+\s',line)):
            del content_arr[i]
        else:
            max_len = (len(line) if (len(line) > max_len) else max_len)
            print(line)
            i += 1
    #
    # determining column sizes (semi-brute force method)
    column_starts = get_column_starts(content_arr,6,max_len)
    #
    # creating ar_line objects
    for line in content_arr:
        ar = ar_line(line,column_starts)
        ar.date = date
        customer_ar_dict[ar.customer_id] = ar
#
# this function determines the column starts of fixed width reports
def get_column_starts(content_arr,start_index,max_len):
    # initializing variables
    column_starts = [0]
    s = start_index
    while True:
        # inital testing 
        for line in content_arr:
            if (not re.match('\s',line[s-1:s])):
                s += 1
                break
        # advancing s until failure
        if (line == content_arr[-1]):
            s += 1
            for line in content_arr:
                if (not re.match('\s',line[s-1:s])):
                    column_starts.append(s-1)
                    break
        #
        if (s > max_len):
            break
    #
    return(column_starts)
#
#
################################################################################
############################# Program Execution ################################
################################################################################
#
#
# initializations
ec_infile = '../EC-Order-Upload.txt'
ar_infile = '../ar_ovchs.txt'
sold_items_list = []
ar_lines_list = []
customer_sales_dict = {}
customer_ar_dict = {}
rep_totals_dict = {}
#
# processing the EC upload file
#!!!!!!!!! I NEED TO CHECK FOR NEG SIGN ON BACK END !!!!!!!!!!
process_ec_order_upload(ec_infile,sold_items_list,customer_sales_dict)
#
# processing the ar_ovchs file
read_ar_ovchs(ar_infile,customer_ar_dict)




