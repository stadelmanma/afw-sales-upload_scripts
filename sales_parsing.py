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
        self.price = make_float(self.col_dict['extended'])
        self.cost  = make_float(self.col_dict['sls_cost-wdeal']) * make_float(self.col_dict['quantity'])     
    #
    def getCol(self,key):
        return(self.col_dict[key])
#
# this stores the line data from the ar_sales report
class sales_line:
    #
    def __init__(self,input_str,col_starts):
        # initializations
        self.rep_id = 0
        self.date = ''
        self.amount = 0.00
        self.col_dict = {}
        #
        # processing input string
        col_names = ['rep_id','junk','avg_days_pay','total','current','bucket_1','bucket_2','bucket_3','bucket_4']
        self.col_dict = line_to_dict(input_str,col_names,col_starts)
        #
        # updating variables
        self.rep_id = self.col_dict['rep_id']
        self.amount = make_float(self.col_dict['total'])
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
        self.col_dict = line_to_dict(input_str,col_names,col_starts)
        #
        # updating variables
        self.rep_id = self.col_dict['rep_id']
        self.customer_id = self.col_dict['customer_id']
        # checking for appended negative sign
        self.amount = make_float(self.col_dict['over'])
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
        self.col_dict = line_to_dict(input_str,col_names,col_starts)
        #
        # updating variables
        self.rep_id = self.col_dict['rep_id']
        #
        self.sales = make_float(self.col_dict['sales'])
        self.credits = make_float(self.col_dict['credits'])
        self.cost = make_float(self.col_dict['cost'])
        self.profit = make_float(self.col_dict['profit'])
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
        self.total_costs  = {}
        self.total_credits = {}
        self.total_profits = {}
        self.total_ar_sales = {}
        self.total_ar = {}
    #
    def incrementDict(self,name,date,amount):
        data_dict = self.__dict__[name]
        try:
            data_dict[date] += amount
        except KeyError:
            self.check_dates(date)
            data_dict[date]  = amount
    #
    def check_dates(self,date):
        for name,dic in self.__dict__.items():
            if (not isinstance(dic,dict)):
                continue
            #
            if (not dic.__contains__(date)):
                dic[date] = 0.0
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
def read_ec_order_upload(infile):
    # reading infile
    upload_file = open(infile,'r')
    content = upload_file.read()
    upload_file.close()
    #
    # splitting lines 
    content_arr = re.split(r'\n',content)
    content_arr = list(filter(None,content_arr))
    #
    sold_items_list = []
    for i in range(len(content_arr)):
        item = sold_item(content_arr[i])
        sold_items_list.append(item)
    #
    return(sold_items_list)
#
#
# ### ### ar_sales File Processing ### ### #
#
#
# this just acts as a driver function to handle all processing of ar_sales file
def process_ar_sales_file(infile,rep_totals_dict):
    #
    # setting up inputs
    line_pat = re.compile(r'\s{1,4}[0-9]+\s+TOTAL\s+')
    def line_func(date,line,column_starts):
        sale = sales_line(line,column_starts)
        sale.date = date
        return(sale)
    #
    entry_list = read_target_report(infile,line_pat,line_func)
    #
    # totaling customer ar into rep
    for entry in entry_list:
        try:
            rep = rep_totals_dict[entry.rep_id]
        except KeyError:
            rep = sales_rep(entry.rep_id)
            rep_totals_dict[entry.rep_id] = rep
        rep.incrementDict('total_ar_sales',entry.date,entry.amount)
#
# ### ### ar_ovchs File Processing ### ### #
#
#
# this just acts as a driver function to handle all processing of ar_ovchs file
def process_ar_ovchs_file(infile,rep_totals_dict):
    #
    # setting up inputs
    line_pat = re.compile(r'\s{1,6}[A-Z0-9]+\s')
    def line_func(date,line,column_starts):
        ar = ar_line(line,column_starts)
        ar.date = date
        return(ar)
    #
    ar_list = read_target_report(infile,line_pat,line_func)
    #
    # totaling customer ar into rep
    for cust in ar_list:
        try:
            rep = rep_totals_dict[cust.rep_id]
        except KeyError:
            rep = sales_rep(cust.rep_id)
            rep_totals_dict[cust.rep_id] = rep
        rep.incrementDict('total_ar',cust.date,cust.amount)
#
#
# ### ### s_wkcomm File Processing ### ### #
#
#
# this just acts as a driver function to handle all processing of s_wkcomm file
def process_s_wkcomm_file(infile,rep_totals_dict):
    #
    # setting up inputs
    line_pat = re.compile(r'^\s{5,}[*]{3}\s+\S+\s+')
    def line_func(date,line,column_starts):
        cl = com_line(line,column_starts)
        cl.date = date
        return(cl)
    #
    comm_list = read_target_report(infile,line_pat,line_func)
    #
    # totaling comm data into rep
    for cl in comm_list:
        try:
            rep = rep_totals_dict[cl.rep_id]
        except KeyError:
            rep = sales_rep(cl.rep_id)
            rep_totals_dict[cl.rep_id] = rep
        #
        rep.incrementDict('total_sales',cl.date,cl.sales)
        rep.incrementDict('total_credits',cl.date,cl.credits)
        rep.incrementDict('total_costs',cl.date,cl.cost)
        rep.incrementDict('total_profits',cl.date,cl.profit)
#
#
# ### ### general use functions ### ### #
#
#
# this function returns a float value from numeric values in reports
def make_float(num_str):
    #
    # removing commans
    num_str = re.sub(',','',num_str)
    #
    # checking for appended negative sign
    if (re.search('-$',num_str)):
        num_str = '-'+re.sub('-$','',num_str)
    #
    num = float(num_str)
    return(num)
#
# this function reads the fixed formatt target reports
def read_target_report(infile,line_pat,line_func):
    # reading infile
    f = open(infile,'r')
    content = f.read()
    f.close()
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
    content_arr = list(filter(line_pat.match,content_arr))
    #
    # determining column sizes 
    column_starts = get_column_starts(content_arr)
    #
    # creating ar_line objects
    output_list = [line_func(date,line,column_starts) for line in content_arr]
    return(output_list)
#
# this function determines the column starts of fixed width reports
def get_column_starts(content_arr):
    # initializing variables
    column_starts = [0]
    padding = re.match(r'\s*',content_arr[0])
    s = padding.end()+1
    max_len = len(content_arr[0])
    while True:
        # inital testing 
        for line in content_arr:
            max_len = (len(line) if (len(line) > max_len) else max_len)
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
def line_to_dict(input_str,col_names,col_starts):
    #
    line_dict = {}
    for i in range(len(col_starts)-1):
        col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
        line_dict[col] = input_str[col_starts[i]:col_starts[i+1]].strip()
    #
    i += 1
    col = (col_names[i] if i < len(col_names) else 'col-'+str(i))
    line_dict[col] = input_str[col_starts[-1]:].strip()
    #
    return(line_dict)
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
        #
        # stepping through dates
        for date in rep.total_sales.keys():
            #
            rep_dict = {
                'rep_id'        : rep.id,
                'date'          : date,
                'total_sales'   : rep.total_sales[date],
                'total_credits' : rep.total_credits[date],
                'total_cost'   : rep.total_costs[date],
                'profit'        : rep.total_profits[date],
                'total_ar_sales': rep.total_ar_sales[date],
                'total_ar'      : rep.total_ar[date],
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
sales_infile = '../ar_sales.txt'
ar_infile = '../ar_ovchs.txt'
com_infile = '../s_wkcomm.txt'
#
ar_sales_list = []
customer_ar_dict = {}
rep_totals_dict = {}
## need to make a script to locate files, the target outputs will have the same name but different numeric extension
## need to create a log to handle all errors and then have that emailed to justin ##
## might be able to do this through a batch process + python 
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
sales_sql  = create_sql('sales_by_customer',sales_dict_list)
rep_sql  = create_sql('sales_rep_data',rep_dict_list)
#
# writting SQL files
f = open('sales_sql_upload.sql','w')
f.write(sales_sql)
f.write('\n')
f.write(rep_sql)
f.close()



