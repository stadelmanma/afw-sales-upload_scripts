# Python 3.4.3 (v3.4.3:9b73f1c3e601, Feb 23 2015, 02:52:03)
# [GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
################################################################################
#
# Description: This module hold functions and classes used to process sales data
#
# Written By: Matthew Stadelman
# Date Written: 2015/01/18
#
# Modified By: Matthew Stadelman
# Last Modifed: 2016/06/12
#
################################################################################
#
#
# module imports
import datetime
import os
import platform
import re
import subprocess
import time
################################################################################
############################## Class Definitions ###############################
################################################################################


class sold_item(dict):
    r"""
    stores an individual items information
    """
    def __init__(self, input_str):
        super().__init__()
        self.col_names = ['rep', 'stamp_op', 'shipname', 'customer_id',
                          'stamp_date', 'ship_date', 'item_number', 'desc',
                          'unit', 'buyer', 'PO_number', 'extended', 'price',
                          'sls_cost-wdeal', 'lot_cost+freight-wdeal', 'quantity',
                          'weight', 'inv_cost-wdeal', 'other']
        self.parse_line(input_str)

    def parse_line(self, line):
        #
        # processing input string
        line_data = re.split(r'\t', line)
        for key, value in zip(self.col_names, line_data):
            self[key] = value.strip()
        #
        # setting additional keys
        self['rep_id'] = self['rep'].split(' ')[0]
        self['customer_id'] = self['customer_id']
        self['date']  = format_date(self['stamp_date'])
        self['amount'] = make_float(self['extended'])
        self['cost']  = make_float(self['sls_cost-wdeal']) * make_float(self['quantity'])


class sales_line(dict):
    r"""
    this stores the line data from the ar_sales report
    """
    def __init__(self, line):
        #
        super.__init__()
        self.col_names  = ['rep_id', 'total', 'current', 'bucket_1',
                          'bucket_2', 'bucket_3', 'bucket_4']
        #
        # processing input string
        self.parse_line(line)

    def parse_line(self,line):
        #
        sales_pat  = [r'^\s*(?P<{}>[A-Z0-9]+)\s*[A-Z]+\s*[0-9?]+\s*']
        sales_pat += [r'(?P<{}>[0-9,]*\.\d\d[-]?)\s*']*6
        #
        # matching input line
        sales_pat = [pat.format(name) for pat, name in zip(sales_pat, col_names)]
        pat = re.compile(''.join(sales_pat), flags=re.I)
        matches = pat.search(line)
        for key in self.col_names:
            self[key] = matches.group(key)
        #
        # updating variables
        self['amount'] = make_float(self['total'])


class com_line(dict):
    r"""
    this stores the line data from the ar_ovchs report
    """
    def __init__(self, line,):
        #
        super().__init__()
        self.col_names = ['rep_id', 'rep_name', 'sales', 'credits', 'cost',
                          'profit', 'margin', 'comm', 'perc']
        #
        # processing input string
        self.parse_line(line)

    def parse_line(self, line):
        #
        # defining pattern array
        comm_pat  = [r'(?P<{}>[0-9A-Z]+)\s*', r'(?P<{}>[0-9A-Z]+(?:\s[0-9A-Z]+)*)\s*']
        comm_pat += [r'(?P<{}>\d*\.\d\d[-]?)\s*']*7
        #
        # matching input line
        comm_pat = [pat.format(name) for pat, name in zip(comm_pat,col_names)]
        pat = re.compile(''.join(comm_pat), flags=re.I)
        matches = pat.search(line)
        for key in self.col_names:
            self[key] = matches.group(key)
        #
        # updating variables
        self['sales'] = make_float(self['sales'])
        self['credits'] = make_float(self['credits'])
        self['cost'] = make_float(self['cost'])
        self['profit'] = make_float(self['profit'])


class sales_rep:
    r"""
    stores sales rep information and totals
    """
    def __init__(self,rep_id):
        self.id = rep_id
        self.date = ''
        self.total_sales = 0.0
        self.total_costs = 0.0
        self.total_credits = 0.0
        self.total_profits = 0.0
        self.total_ar_sales = 0.0
        self.total_ar = 0.0
#
#
################################################################################
############################ Function Definitions ##############################
################################################################################
#
# ### ### EC Upload File Processing ### ### #


def read_ec_order_upload(infile):
    r"""
    this processes the ec upload file and populates the sold_items_list
    """
    # reading infile
    upload_file = open(infile,'r')
    content = upload_file.read()
    upload_file.close()
    #
    # splitting lines
    content_arr = re.split(r'\n',content)
    content_arr = [line for line in content_arr if line]
    #
    sold_items_list = []
    for i in range(len(content_arr)):
        item = sold_item(content_arr[i])
        sold_items_list.append(item)
    #
    return sold_items_list
#
#
# ### ### ar_sales File Processing ### ### #


def process_ar_sales_file(infile,rep_totals_dict):
    r"""
    this just acts as a driver function to handle all processing of ar_sales file
    """
    #
    # setting up inputs
    line_pat = re.compile(r'\s{1,4}[0-9]+\s+TOTAL\s+')
    def line_func(line):
        sale = sales_line(line,column_starts)
        return sale
    #
    entry_list = read_target_report(infile,line_pat,sales_line)
    #
    # totaling customer ar into rep
    for entry in entry_list:
        try:
            rep = rep_totals_dict[entry['rep_id']]
        except KeyError:
            rep = sales_rep(entry['rep_id'])
            rep_totals_dict[entry['rep_id']] = rep
        rep.total_ar_sales += entry['amount']
#
# ### ### ar_ovchs File Processing ### ### #


def process_ar_ovchs_file(infile,rep_totals_dict):
    r"""
    this just acts as a driver function to handle all processing of ar_ovchs file
    """
    #
    # reading file
    pat = r'START OF SALESREP[ ]*?([A-Z0-9]+)\s.*?(?:.*?\n)*?.*?SALESREP TOTAL:.*?(\d*\.\d\d[-]?)'
    with open(infile,'r') as f:
        content = f.read()
        totals = re.findall(pat,content)
    #
    # putting total ar into rep objects
    for ar in totals:
        try:
            rep = rep_totals_dict[ar[0].strip()]
        except KeyError:
            rep = sales_rep(ar[0].strip())
            rep_totals_dict[ar[0].strip()] = rep
        rep.total_ar = make_float(ar[1])
#
#
# ### ### s_wkcomm File Processing ### ### #


def process_s_wkcomm_file(infile,rep_totals_dict):
    r"""
    this just acts as a driver function to handle all processing of s_wkcomm file
    """
    #
    # getting date from commission infile
    f = open(infile,'r')
    content = f.read()
    f.close()
    m = re.search(r'From\s+[0-9/]+\s+to\s+([0-9/]+)',content)
    date = format_date(m.group(1))
    for rid in rep_totals_dict:
        rep = rep_totals_dict[rid]
        rep.date = date
    #
    # setting up inputs
    line_pat = re.compile(r'^\s{5,}[*]{3}\s+\S+\s+')
    def line_func(line):
        cl = com_line(line)
        return cl
    #
    comm_list = read_target_report(infile,line_pat,com_line)
    #
    # totaling comm data into rep
    for cl in comm_list:
        try:
            rep = rep_totals_dict[cl['rep_id']]
        except KeyError:
            rep = sales_rep(cl['rep_id'])
            rep.date = date
            rep_totals_dict[cl['rep_id']] = rep
        #
        rep.total_sales += cl.sales
        rep.total_credits += cl.credits
        rep.total_costs += cl.cost
        rep.total_profits += cl.profit
#
#
# ### ### general use functions ### ### #


def get_filenames():
    r"""
    this function searches the local directory for the most recent upload files
    """
    #
    if (platform.system().lower() == 'windows'):
        list_dir = subprocess.Popen(['dir', '/b', '/o:gn'], stdout=subprocess.PIPE, shell=True)
    else:
        list_dir =  subprocess.Popen('ls', stdout=subprocess.PIPE, shell=True)
    #
    contents = list_dir.stdout.read()
    contents = contents.decode()
    #
    # finding all matching files
    ar_sales_files = re.findall('(ar_sales\.[0-9]*)',contents)
    ar_ovchs_files = re.findall('(ar_ovchs\.[0-9]*)',contents)
    s_wkcomm_files = re.findall('(s_wkcomm\.[0-9]*)',contents)
    #
    file_dict = {
        'ar_sales' : ar_sales_files,
        'ar_ovchs' : ar_ovchs_files,
        's_wkcomm' : s_wkcomm_files
    }
    #
    # testing creation dates
    for report in file_dict:
        files = list(filter(None,file_dict[report]))
        files = [f.strip() for f in files]
        test_date = get_report_date(files[0])
        file_dict[report] = files[0]
        for filename in files:
            date = get_report_date(filename)
            if date > test_date:
                file_dict[report] = filename
                test_date = date
    #
    return file_dict


def get_report_date(filename):
    r"""
    this function reads a target report and pulls the date from the header
    """
    #
    with open(filename,'r') as f:
        content = f.read()
    #
    # splitting lines
    content_arr = re.split(r'\n',content)
    content_arr = [line for line in content_arr if line]
    #
    date_line = content_arr[1]
    date = re.search(r'(\d\d/\d\d/\d\d)',date_line).group(1)
    date = time.strptime('12/19/15','%m/%d/%y')
    #
    return time.mktime(date)


def make_float(num_str):
    r"""
    this function returns a float value from numeric values in reports
    """
    #
    # removing commas
    num_str = re.sub(',','',num_str)
    #
    # checking for appended negative sign
    if re.search('-$',num_str):
        num_str = '-'+re.sub('-$','',num_str)
    #
    num = float(num_str)
    return num


def format_date(date_str):
    r"""
    this function converts a date into proper SQL format
    """
    # converting to date object
    date = datetime.datetime.strptime(date_str,'%x')
    # back converting to string
    date_str = date.strftime('%Y-%m-%d')
    #
    return date_str


def read_target_report(infile,line_pat,line_func):
    r"""
    this function reads the fixed format target reports
    """
    # reading infile
    f = open(infile,'r')
    content = f.read()
    f.close()
    #
    # splitting lines
    content_arr = re.split(r'\n',content)
    content_arr = [line for line in content_arr if line]
    #
    # filtering uneeded lines
    content_arr = list(filter(line_pat.match,content_arr))
    #
    # creating ar_line objects
    output_list = [line_func(line) for line in content_arr]
    return output_list
#
#
# ### ### SQL generation ### ### #


def make_sales_sql_dicts(sold_items_list):
    r"""
    this function pulls required information from the sold item class
    """
    #
    sales_dict_list = []
    #
    # stepping through items
    for item in sold_items_list:
        item_dict = {
            'customer_id'   : item['customer_id'],
            'date'          : item['date'],
            'stamp_op'      : item['stamp_op'],
            'buyer'         : item['buyer'],
            'amount'        : item['amount'],
            'entering_user' : 'python-upload',
            'entry_status'  : 'submitted',
            'sales_data_last_modified_by' : '',
            'sales_data_last_modified' : '',
        }
        #
        sales_dict_list.append(item_dict)
    return sales_dict_list


def make_rep_sql_dicts(rep_totals_dict):
    r"""
    Creates SQL dictionaries from sales rep data
    """
    #
    rep_dict_list = []
    #
    # stepping through reps
    for key in rep_totals_dict.keys():
        rep = rep_totals_dict[key]
        #
        rep_dict = {
            'rep_id'        : rep.id,
            'date'          : rep.date,
            'total_sales'   : rep.total_sales,
            'total_credits' : rep.total_credits,
            'total_cost'    : rep.total_costs,
            'profit'        : rep.total_profits,
            'total_ar_sales': rep.total_ar_sales,
            'total_ar'      : rep.total_ar,
            'entering_user' : 'python-upload',
            'entry_status'  : 'submitted',
            'sales_rep_data_last_modified_by'     : '',
            'sales_rep_data_last_modified' : '',
        }
        #
        rep_dict_list.append(rep_dict)
    return rep_dict_list


def create_sql(table,data):
    r"""
    this creates a sql statement from a dictionary input using the keys as columns
    """
    #
    # initializaing variables
    sql = ''
    stride = 200 # how many insert statements to pack together
    keyset = list(data[0].keys())
    for i in range(len(data)):
        dic = data[i]
        # making insert statement
        if i%stride == 0:
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
    return sql
