"""
/**
 * @file    M2M.py
 * @brief   M2M swarm to get send and receive data from excel sheet and call appropriate swarmlet with 
 *          configuration and paylod data
 *
 * Copyright (c) 2016 Arrayent Incorporated.  All rights reserved.
 * Software License Agreement
 *
 * The software is owned by Arrayent Incorporated and/or its suppliers, and is protected
 * under applicable copyright laws.
 *
 * IN NO EVENT SHALL ARRAYENT INCORPORATED BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
 * INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF THE USE OF THIS
 * SOFTWARE AND ITS DOCUMENTATION, EVEN IF ARRAYENT INCORPORATED HAS BEEN ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * ARRAYENT INCORPORATED  SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE SOFTWARE AND
 * ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED "AS IS". ARRAYENT
 * INCORPORATED HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR
 * MODIFICATIONS.
 *
 */
"""

import xlrd
from itertools import product
import os
import re
import binascii
import ast
import sys
            
COMM_LINE_ARG_COUNT = 4

# String to compare in excel to get device credentials 
DEVICE_NAME = "Device Name"
DEVICE_PASSWORD = "Device Password"
DEVICE_AES_KEY = "Device AES Key"
PRODUCT_AES_KEY = "Product AES Key"
PRODUCT_ID = "Product ID"
LOAD_BALANCER = "Load Balancer"

# String to compare in excel to get whether call send or receive swarmlet
SEND_SWARMLET = "Send"
RECEIVE_SWARMLET = "Receive"

# String to comapre in excel to get Key and it's value size so swarmlet can create binary payload
# with correct value(As per the "ArrayentM2M.pdf" value size is depend upon key)
KEY_VALUE_SIZE = "Key Value size Pair"

# String to compare in excel to get Description of perticular test case to be print on cosole
# during test case execution
DESCRIPTION = "Description"

#M2M API that are supported
API_ADMIN               = 0xF0
API_ISP                 = 0xF1
API_APPLIANCE_IDENTITY  = 0xF2
API_SUBSCRIBE           = 0xF3
API_DATE_TIME           = 0xF4
API_RESET               = 0xF5
API_COMM_CONTROL_KVP    = 0xF6

#M2M OPCODE for "CommandControl_KVP" message type
OP_GET_URI              = 0x01
OP_SUBSCRIBE            = 0x02
OP_GET_KVP              = 0x03
OP_SET_KVP              = 0x04
OP_PUB_URI              = 0x81
OP_PUB_SUB_RESULT       = 0x82
OP_PUB_KVP              = 0x83
OP_PUB_SET_KVP_RESULT   = 0x84



Config_dict = {}
key_value_size_dict = {}
""" comment define defination of GET_CELL_VALUE """
GET_CELL_VALUE = lambda row, col, sheetname: sheetname.cell_value(row, col)


def getDeviceCredentials(sheet):
    '''
    Get Device Credentials from Excel sheet
    :param sheet: Sheet Name
    :return: None
    '''
    # go through each cell
    for row, col in product(range(sheet.nrows), range(sheet.ncols)):
        # check if cell title matches "Input Param"
        if sheet.cell(row, col).value == DEVICE_NAME:
              Config_dict[DEVICE_NAME] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == DEVICE_PASSWORD:
              Config_dict[DEVICE_PASSWORD] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == DEVICE_AES_KEY:
              Config_dict[DEVICE_AES_KEY] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == PRODUCT_AES_KEY:
              Config_dict[PRODUCT_AES_KEY] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == PRODUCT_ID:
              Config_dict[PRODUCT_ID] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == LOAD_BALANCER:
              Config_dict[LOAD_BALANCER] = GET_CELL_VALUE(row, col + 1, sheet)
        elif sheet.cell(row, col).value == KEY_VALUE_SIZE:
              key_value_size_sting = GET_CELL_VALUE(row, col + 1, sheet)
              global key_value_size_dict
              key_value_size_dict = ast.literal_eval(key_value_size_sting)


def getDeviceConfigString():
    '''
    Get Device Configuration string
    :return: Configuration string
    '''
    config_str = " -an " + Config_dict[DEVICE_NAME]
    config_str = config_str + " -ap " + str(Config_dict[DEVICE_PASSWORD])
    config_str = config_str + " -ad " + str(Config_dict[DEVICE_AES_KEY])
    config_str = config_str + " -ak " + str(Config_dict[PRODUCT_AES_KEY])
    config_str = config_str + " -ai " + str(int(Config_dict[PRODUCT_ID]))
    config_str = config_str + " -al " + Config_dict[LOAD_BALANCER]
    return config_str


def getTestCaseRawColumn(sheet):
    '''
    Get Row and column number of Test case
    :param sheet: Sheet Name
    :return: roe no., column no.
    '''
    # go through each cell
    for row, col in product(range(sheet.nrows), range(sheet.ncols)):
        # check if cell title matches "Input Param"
        if sheet.cell(row, col).value == DESCRIPTION:
            return row, col



def getTheSheetHandleOfExcelSheetsInWorkBook(filename):
    '''
    Get the sheet handle of all excel sheets present in all workbooks
    :param filename:
    :return:
    '''
    # Excel sheet handler dictionary
    sheetHndldict = {}
    # Get Excel file handler
    excelWorkbook = xlrd.open_workbook(filename)
    # store Excel sheet handle in dictionary
    for sheet_hanler in excelWorkbook.sheets():
        sheetHndldict[sheet_hanler.name] = sheet_hanler
    return sheetHndldict;


def getOpcodeGetUriPayload(payload_data):
    '''
    Get M2M Payload for Get Uri message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    if len(payload_data) is not 0:
        dest_node = int(payload_data, 16)
        dest_node_str = "%0.2X" % dest_node
        payload_str = payload_str + dest_node_str

    return payload_str

def getOpcodeSubscribePayload(payload_data):
    '''
    Get M2M Payload for Subscribe message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_str = ''
    payload_len = len(payload_tuple)

    if temp_iter < payload_len:
        source_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + source_node
    else:
        return payload_str

    temp_iter += 1

    if temp_iter < payload_len:
        key_value_rcvpad_list = payload_tuple[temp_iter]
        j = 0
        for i in range(len(key_value_rcvpad_list)):
            if j < len(key_value_rcvpad_list[i]):
                payload_str = payload_str + ("%0.8X" % key_value_rcvpad_list[i][j])
            else:
                return payload_str
            j += 1

            if j < len(key_value_rcvpad_list[i]):
                payload_str = payload_str + ("%0.4X" % key_value_rcvpad_list[i][j])
            else:
                return payload_str
            j += 1

            if j < len(key_value_rcvpad_list[i]):
                payload_str = payload_str + ("%0.4X" % key_value_rcvpad_list[i][j])
            else:
                return payload_str
            j = 0
    return payload_str


def getOpcodeGetKvpPayload(payload_data):
    '''
    Get M2M Payload for Get Kvp message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_len = len(payload_tuple)

    if temp_iter < payload_len:
        dest_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + dest_node
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        key_list = payload_tuple[temp_iter]
        for i in range(len(key_list)):
            payload_str = payload_str + ("%0.8X" % key_list[i][0])
    return payload_str




def getOpcodeSetKvpPayload(payload_data):
    '''
    Get M2M Payload for Set Kvp message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_len = len(payload_tuple)
    if temp_iter < payload_len:
        dest_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + dest_node
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        transaction_id = "%0.4X" % payload_tuple[temp_iter]
        payload_str = payload_str + transaction_id
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        key_value_list = payload_tuple[temp_iter]
        j = 0
        for i in range(len(key_value_list)):
            if j < len(key_value_list[i]):
                payload_str = payload_str + ("%0.8X" % key_value_list[i][j])
            else:
                return payload_str
            j += 1

            if j < len(key_value_list[i]):
                value = "%X" % key_value_list[i][j]
                value_string = value.zfill(key_value_size_dict[key_value_list[i][j - 1]] * 2)
                payload_str = payload_str + value_string
            else:
                return payload_str
            j = 0
    return payload_str

def getOpcodePubUriPayload(payload_data):
    '''
    Get M2M Payload for Publish Uri message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_len = len(payload_tuple)
    if temp_iter < payload_len:
        source_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + source_node
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        namespace_id = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + namespace_id
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        uri = (binascii.b2a_hex(binascii.a2b_qp(payload_tuple[temp_iter]))).decode('ascii')
        length = (len(source_node)/2) + (len(namespace_id)/2) + (len(uri)/2)
        payload_str = payload_str + uri
    return payload_str

def getOpcodePubSubResultPayload(payload_data):
    '''
    Get M2M Payload for Publish Subscribed Result message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_len = len(payload_tuple)
    if temp_iter < payload_len:
        source_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + source_node
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        key_value_list = payload_tuple[temp_iter]
        j = 0
        for i in range(len(key_value_list)):
            if j < len(key_value_list[i]):
                payload_str = payload_str + ("%0.8X" % key_value_list[i][j])
            else:
                return payload_str
            j += 1

            if j < len(key_value_list[i]):
                payload_str = payload_str + ("%0.2X" % key_value_list[i][j])
            else:
                return payload_str
            j = 0
    return payload_str

def getOpcodePubKvpPayload(payload_data):
    '''
    Get M2M Payload for Publish Kvp message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''

    key_value = payload_data.replace('[','').replace(']','').replace('0x','').replace(' ', '')
    key_value = key_value.split(',')
    for temp_iter in range(len(key_value)):
        payload_str = payload_str + key_value[temp_iter]
    return payload_str
        
            

def getOpcodePubSetKvpResultPayload(payload_data):
    '''
    Get M2M Payload for Publish Set Kvp Result message opcode
    :param payload_data: Payload data
    :return: Payload string
    '''
    payload_str = ''
    payload_tuple = ast.literal_eval(payload_data)
    temp_iter = 0
    payload_len = len(payload_tuple)
    if temp_iter < payload_len:
        source_node = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + source_node
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        transaction_id = "%0.4X" % payload_tuple[temp_iter]
        payload_str = payload_str + transaction_id
    else:
        return payload_str
    temp_iter += 1

    if temp_iter < payload_len:
        result = "%0.2X" % payload_tuple[temp_iter]
        payload_str = payload_str + result
    return payload_str


def getCaseExecutionString(sheet, row, col, config_string, send_file_path, receive_file_path):
    '''
    Get Execution string that can be use to run swarmlet with configuration as per the test case
    :param sheet: Sheet Handler
	:param row: Test case Row number
	:param col: Test case Column number
	:param config_string: Device credentials config string
	:param send_file_path: path to M2M send swarmlet 
    :param receive_file_path: path to M2M receive swarmlet
    :return: Execution string
    '''
    string = "./"
    payload_str = ""
    col += 1
    m2m_swarmlet = GET_CELL_VALUE(row, col, sheet)
    if len(m2m_swarmlet) is 0:
        return

    if m2m_swarmlet == "Send":
        string = string + send_file_path
    elif m2m_swarmlet == "Receive":
        string = string + receive_file_path

    string = string +config_string
    col += 1
    m2m_length = GET_CELL_VALUE(row, col, sheet)
    if len(m2m_length) is not 0:
        string = string + " -sl " + m2m_length

    col += 1
    m2m_api = GET_CELL_VALUE(row, col, sheet)
    if len(m2m_api) is not 0:
        string = string + " -sa " + m2m_api
    else:
        return string

    col += 1
    m2m_opcode = GET_CELL_VALUE(row, col, sheet)
    if len(m2m_opcode) is not 0:
        string = string + " -so " + m2m_opcode
    else:
        return string

    col += 1
    payload_length = GET_CELL_VALUE(row, col, sheet)


    col += 1
    payload_data = GET_CELL_VALUE(row, col, sheet)
    if len(payload_data) is 0:
        return string

    if m2m_swarmlet == "Receive":
        key_value_size_str = "0x"
        for key, value in key_value_size_dict.items():
            key_value_size_str = key_value_size_str + ("%0.8X" % key) + ("%0.2X" % value)
        string = string + " -sv " + key_value_size_str

    if int(m2m_api, 16) is API_COMM_CONTROL_KVP:
        if int(m2m_opcode, 16) is OP_GET_URI:
            payload_str = getOpcodeGetUriPayload(payload_data)

        elif int(m2m_opcode, 16) is OP_SUBSCRIBE:
            payload_str = getOpcodeSubscribePayload(payload_data)
            
        elif int(m2m_opcode, 16) is OP_GET_KVP:
            payload_str = getOpcodeGetKvpPayload(payload_data)
            
        elif int(m2m_opcode, 16) is OP_SET_KVP:
            payload_str = getOpcodeSetKvpPayload(payload_data)


        elif int(m2m_opcode, 16) is OP_PUB_URI:
            payload_str = getOpcodePubUriPayload(payload_data)

        elif int(m2m_opcode, 16) is OP_PUB_SUB_RESULT:
            payload_str = getOpcodePubSubResultPayload(payload_data)


        elif int(m2m_opcode, 16) is OP_PUB_KVP:
            payload_str = getOpcodePubKvpPayload(payload_data)


        elif int(m2m_opcode, 16) is OP_PUB_SET_KVP_RESULT:
            payload_str = getOpcodePubSetKvpResultPayload(payload_data)

        if len(payload_length) is 0:
            payload_length = "0x%0.4X" % (len(payload_str)/2)

        string = string + " -sp " + payload_length + payload_str

    else:
        string = string + " -sp " + "'" + GET_CELL_VALUE(row, col, sheet) + "'"
    return string


if __name__ == '__main__':   
    gsheetHandlerDict = {}
    if len(sys.argv) != COMM_LINE_ARG_COUNT:
        print("Usage: python3 M2M.py test.xls ../M2M_send/M2M_send ../M2M_receive/M2M_receive")
    else:
        gsheetHandlerDict = getTheSheetHandleOfExcelSheetsInWorkBook(sys.argv[1])
        getDeviceCredentials(gsheetHandlerDict["Sheet1"])
        config_str = getDeviceConfigString()
        case_row, case_column = getTestCaseRawColumn(gsheetHandlerDict["Sheet1"])
        
        i = 1
        while gsheetHandlerDict["Sheet1"].nrows > case_row + i:
            execute_string = getCaseExecutionString(gsheetHandlerDict["Sheet1"], case_row + i, case_column, config_str, sys.argv[2], sys.argv[3])
            print('\nExecuting Test case "' + GET_CELL_VALUE(case_row + i, case_column, gsheetHandlerDict["Sheet1"]) + '"\n')
            os.system(execute_string)
            cli_in = input('Please press any key to continue...')  
            i += 1

