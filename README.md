# Get_License_Details
Get the License details based on the chassis/server IP and return the results into the xls/csv file.
# Key Features
Get the license details based on the chassis/server IP
Generate Excel/CSV file along with the license details based on the input.
# Required Python Packages
pip install pandas\
pip install logging\
pip install requests\
pip install json\
pip install time
# Import the packages
from get_license_details import IxChassisDetails
# Run script
from get_license_details import IxChassisDetails\
#Get the License details based on the API server IP (activation_code parameter is mandatory)
session = IxChassisDetails("admin", "admin", server_ip="10.39.71.237", ixnetwork_type="linux")
session.csv_xlsx_retrieve_license('chassis_license', file_format='csv', activation_code=['7724-8DB6-A2F0-A56C', 'C415-2B94-C0ED-3E56', '9C47-D170-353C-947F', 'C1FA-E892-F27E-28FB', '8E35-595C-5214-7D69'])

#Get the License details based on the chassis IP (activation_code parameter is optional)\
session = IxChassisDetails("admin", "admin", chassis_ip="10.39.64.169")
session.csv_xlsx_retrieve_license('chassis_license', file_format='csv')
# Supported Server Versions
Linux API server\
#Currently we dont have support on Windows because the License utility not integrated on the windows API server.
