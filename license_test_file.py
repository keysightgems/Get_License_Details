import pandas as pd
from get_license_details import IxChassisDetails
from datetime import datetime
# Get the License details based on the API server IP
df = pd.read_excel('license_input.xlsx')
excelDict = df.to_dict()
serverIP = excelDict['server_ip'][0]
ixnetworkType = excelDict['ixnetwork_type'][0]
fileName = excelDict['file_name'][0]
fileFormat = excelDict['file_format'][0]
activationCode = [value for key, value in excelDict['activationCode'].items()]
print("Connecting the session")
session = IxChassisDetails("admin", "admin", server_ip=serverIP, ixnetwork_type=ixnetworkType)
#Get the License details based on the chassis IP
# session = IxChassisDetails("admin", "admin", chassis_ip="10.39.64.169")
# activation_code (optional) parameter requires if liocense details getting based on the API server else not required
#['7724-8DB6-A2F0-A56C', 'C415-2B94-C0ED-3E56', '9C47-D170-353C-947F', 'C1FA-E892-F27E-28FB', '8E35-595C-5214-7D69']
print("Getting the license activation code details...")
session.csv_xlsx_retrieve_license(fileName, file_format=fileFormat, activation_code=activationCode)
print("Completed execution and generated the file")
# session.csv_xlsx_retrieve_license('chassis_license', file_format='csv')
