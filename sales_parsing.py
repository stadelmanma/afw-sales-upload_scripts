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
        col_names = ['rep','stamp_op','shipname','customer_id','stamp_date','ship_date','item_number','desc','unit','buyer','PO_number','extended','price','sls_cost-wdeal','lot_cost+freight-wdeal','quantity','weight','inv_cost-wdeal','other']
        input_arr = re.split(r'\t',input_str)
        for i in range(len(input_arr)):
            col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
            self.col_dict[col] = input_arr[i].strip()
        #
        # updating variables
        self.rep_id = self.col_dict['rep'].split(' ')[0]  #these will be replaced with useful col names
        self.customer_id = self.col_dict['customer_id']
        self.date  = self.col_dict['stamp_date']
        self.price = float(self.col_dict['extended'])
        self.cost  = float(self.col_dict['sls_cost-wdeal']) * float(self.col_dict['quantity'])     
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
        #
        # processing input string
        col_names = ['customer_id','name','desc','address','phone','rep_id','city','state','over','ar_ttl']
        for i in range(len(col_starts)-1):
            col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
            self.col_dict[col] = input_str[col_starts[i]:col_starts[i+1]].strip()
        i += 1
        col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
        self.col_dict[col] = input_str[col_starts[-1]:].strip()
        #
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
# this stores the line data from the ar_ovchs report
class com_line:
    #
    def __init__(self,input_str,col_starts):
        # initializations
        self.rep_id = 0
        self.date = ''
        self.sales = 0.00
        self.credits = 0.00
        self.cost = 0.00
        self.profit = 0.00
        self.col_dict = {}
        #
        # processing input string
        col_names = ['spacer','rep_id','rep_name','sales','credits','cost','profit','margin','comm','perc']
        for i in range(len(col_starts)-1):
            col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
            self.col_dict[col] = input_str[col_starts[i]:col_starts[i+1]].strip()
        i += 1
        col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
        self.col_dict[col] = input_str[col_starts[-1]:].strip()
        #
        # updating variables
        self.rep_id = self.col_dict['rep_id']
        #
        # checking for appended negative sign
        if (re.search('-$',self.col_dict['sales'])):
            self.col_dict['sales'] = '-'+re.sub('-$','',self.col_dict['sales'])
        self.sales = float(self.col_dict['sales'])
        #
        if (re.search('-$',self.col_dict['credits'])):
            self.col_dict['credits'] = '-'+re.sub('-$','',self.col_dict['credits'])
        self.credits = float(self.col_dict['credits'])
        #
        if (re.search('-$',self.col_dict['cost'])):
            self.col_dict['cost'] = '-'+re.sub('-$','',self.col_dict['cost'])
        self.cost = float(self.col_dict['cost'])
        #
        if (re.search('-$',self.col_dict['profit'])):
            self.col_dict['profit'] = '-'+re.sub('-$','',self.col_dict['profit'])
        self.cost = float(self.col_dict['profit'])
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
    #
    def incrementSales(self,date,price,cost):
        try:
            self.daily_sales[date] += price
            self.daily_costs[date] += cost
        except KeyError:
            self.daily_sales[date]  = price
            self.daily_costs[date]  = cost
#
# stores sales rep information and totals 
class sales_rep:
    #
    def __init__(self,rep_id):
        self.id = rep_id
        self.total_sales  = {}
        self.total_cost  = {}
        self.total_credits = {}
        self.total_profits = {}
        self.total_ar = {}
        self.total_ar_sales = {}
    #
    def incrementSales(self,date,price,cost):
        try:
            self.total_sales[date] += price
        except KeyError:
            self.check_dates(date)
            self.total_sales[date]  = price
    #
    def incrementCredits(self,date,amount):
        try:
            self.total_credits[date] += amount
        except KeyError:
            self.check_dates(date)
            self.total_credits[date]  = amount
    #
    def incrementCosts(self,date,amount):
        try:
            self.total_credits[date] += amount
        except KeyError:
            self.check_dates(date)
            self.total_credits[date]  = amount
    #
    
    def incrementProfits(self,date,amount):
        try:
            self.total_profits[date] += amount
        except KeyError:
            self.check_dates(date)
            self.total_profits[date]  = amount
    #
    def incrementArSales(self,date,amount):
        try:
            self.total_ar_sales[date] += amount
        except KeyError:
            self.check_dates(date)
            self.total_ar_sales[date]  = amount
    #
    def incrementAr(self,date,amount):
        try:
            self.total_ar[date] += amount
        except KeyError:
            self.check_dates(date)
            self.total_ar[date]  = amount
    #
    def check_dates(self,date):
        if (not self.total_sales.__contains__(date)):
             self.total_sales[date] = 0.0
        if (not self.total_cost.__contains__(date)):
             self.total_cost[date] = 0.0
        if (not self.total_ar_sales.__contains__(date)):
             self.total_ar_sales[date] = 0.0
        if (not self.total_ar.__contains__(date)):
             self.total_ar[date] = 0.0
        if (not self.total_credits.__contains__(date)):
             self.total_credits[date] = 0.0
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
# this function totals up AR by rep
def rep_ar_totals(customer_ar_dict,rep_totals_dict):
    #
    for cust in customer_ar_dict:
        cust = customer_ar_dict[cust]
        try:
            rep = rep_totals_dict[cust.rep_id]
        except KeyError:
            rep = sales_rep(cust.rep_id)
            rep_totals_dict[cust.rep_id] = rep
        rep.incrementAr(cust.date,cust.amount)
#
# this just acts as a driver function to handle all processing of ar_ovchs file
def process_ar_ovchs_file(ec_infile,customer_ar_dict,rep_totals_dict):
    #
    # reading EC upload file
    read_ar_ovchs(ar_infile,customer_ar_dict)
    #
    # totaling customer ar into rep
    rep_ar_totals(customer_ar_dict,rep_totals_dict)
#
#
# ### ### s_wkcomm File Processing ### ### #
#
#
# this function reads the s_wkcomm file
def read_s_wkcomm(com_infile,com_line_list):
    # reading infile
    com_file = open(com_infile,'r')
    content = com_file.read()
    com_file.close()
    #
    # splitting by form feed characters (\x0c)
    rep_page = re.split(r'\x0c',content)[1]
    #
    # splitting rep page by newlines
    line_arr = rep_page.split('\n')
    line_arr = list(filter(None,line_arr))
    #
    # getting date from header
    date = re.split('\s{2,}',line_arr[1])[2]
    date = date.strip()
    # removing header and totals lines
    del line_arr[0:6]
    del line_arr[-1]
    del line_arr[-1]
    #
    column_starts = get_column_starts(line_arr,24,len(line_arr[0])+5)
    #
    for line in line_arr:
        cl = com_line(line,column_starts)
        cl.date = date
        com_line_list.append(cl)
#
# this function adds the credits line to the rep object
def rep_comm_totals(com_line_list,rep_totals_dict):
    #
    for cl in com_line_list:
        try:
            rep = rep_totals_dict[cl.rep_id]
        except KeyError:
            rep = sales_rep(cl.rep_id)
            rep_totals_dict[cl.rep_id] = rep
        #
        rep.incrementSales(cl.date,cl.sales)
        rep.incrementCredits(cl.date,cl.credits)
        rep.incrementCosts(cl.date,cl.costs)
        rep.incrementProfits(cl.date,cl.profit)
#
# this just acts as a driver function to handle all processing of s_wkcomm file
def process_s_wkcomm_file(com_infile,com_line_list,rep_totals_dict):
    #
    # reading EC upload file
    read_s_wkcomm(com_infile,com_line_list)
    #
    # totaling customer ar into rep
    rep_comm_totals(com_line_list,rep_totals_dict)
#
#
# ### ### SQL generation ### ### #
#
#
# this function pulls the meaty bits from the objects stored in the customer and rep classes
def make_sales_sql_dicts(sold_items_list):
    #
    # defining columns
    #
    sales_dict_list = []
    #
    # stepping through customers
    for item in sold_items_list:
        item_dict = {
            'customer_id'   : item.customer_id,
            'date'          : item.date,
            'stamp_op'      : item.getCol('stamp_op'),
            'buyer'         : item.getCol('buyer'),
            'amount'        : item.price,
            'entering_user' : 'python-upload',
            'entry_status'  : 'submitted',
            'admin_fix'     : '',
            'admin_fix_timestamp' : '',
        }
        #
        sales_dict_list.append(item_dict) 
    return(sales_dict_list)
#
#   
def make_rep_sql_dicts(rep_totals_dict):
    #
    rep_dict_list = []   
    #
    # stepping through reps
    for key in rep_totals_dict.keys():
        rep = rep_totals_dict[key]
        # stepping through dates
        keys = list(rep.ar_total.keys())
        for date in keys:
            try:
                ar = rep.ar_total[date]
            except KeyError:
                ar = 0.0
            try:
                credits = rep.credit_total[date]
            except KeyError:
                credits = 0.0
            #
            rep_dict = {
                'rep_id'        : rep.id,
                'date'          : date,
                'total_ar'      : ar,
                'total_credits' : credits,
                'entering_user' : 'python-upload',
                'entry_status'  : 'submitted',
                'admin_fix'     : '',
                'admin_fix_timestamp' : '',
            }
            #
            rep_dict_list.append(rep_dict)  
    return(rep_dict_list)
#
# this creates a sql statement from a dctionary input using the keys as colunns
def create_sql(table,data):
    #
    # initializaing variables
    sql = ''
    stride = 50 # how many insert statements to pack together
    keyset = list(data[0].keys())
    for i in range(len(data)):
        dic = data[i]
        # making insert statement
        if (i%stride == 0):
            sql += 'INSERT INTO `'+table+'` '
            cols = ['`'+col+'`' for col in keyset]
            cols = ','.join(cols)
            sql += '('+cols+') VALUES \n'
        else:
            sql += ',\n'
        # 
        vals = ["'"+str(dic[key])+"'" for key in keyset]
        vals = ','.join(vals)
        sql += '('+vals+')'
        sql += (';\n' if ((i+1)%stride == 0 and (i+1 < len(data))) else '')
    sql += ';'
    return(sql)        
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
com_infile = '../s_wkcomm.txt'
sold_items_list = []
com_line_list = []
customer_sales_dict = {}
customer_ar_dict = {}
rep_totals_dict = {}
## need to make a script to locate files, the target outputs will have the same name but different numeric extension
## need to create a log to handle all errors and then have that emailed to justin ##
## might be able to do this through a batch process + python 
#
# processing the EC upload file
process_ec_order_upload(ec_infile,sold_items_list,customer_sales_dict)
#
# processing the ar_ovchs file
process_ar_ovchs_file(ec_infile,customer_ar_dict,rep_totals_dict)
#
# processing the s_wkcomm file
process_s_wkcomm_file(com_infile,com_line_list,rep_totals_dict)
#
# creating sql upload statments
sales_dict_list = make_sales_sql_dicts(sold_items_list)
rep_dict_list  = make_rep_sql_dicts(rep_totals_dict)
sales_sql  = create_sql('sales_by_customer',sales_dict_list)
print(sales_sql)


