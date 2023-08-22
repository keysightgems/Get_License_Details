from get_license_details import IxChassisDetails
from datetime import datetime
# Get the License details based on the API server IP
session = IxChassisDetails("admin", "admin", server_ip="10.39.71.237", ixnetwork_type="linux")
#Get the License details based on the chassis IP
# session = IxChassisDetails("admin", "admin", chassis_ip="10.39.64.169")

start = datetime.now()
# activation_code (optional) parameter requires if liocense details getting based on the API server else not required
session.csv_xlsx_retrieve_license('chassis_license', file_format='csv', activation_code=['7724-8DB6-A2F0-A56C', 'C415-2B94-C0ED-3E56', '9C47-D170-353C-947F', 'C1FA-E892-F27E-28FB', '8E35-595C-5214-7D69'])
# session.csv_xlsx_retrieve_license('chassis_license', file_format='csv')
end = datetime.now()
print("total:",start, end)
