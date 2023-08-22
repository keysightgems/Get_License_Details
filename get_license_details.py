#!/usr/bin/python

import logging
import json
import time
import pandas as pd
import requests

# Do not show warning related to unverified ssl certificates
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except: pass


class IxRestException(Exception): pass

class IxChassisDetails(object):
    """
    class for handling HTTP requests against Ixia Chassis
    """
    def __init__(self, user_name, user_pass, ixnetwork_type="windows", host_name=None, server_ip=None, chassis_ip=None, api_key=None):
        """
        Get the chassis license details
        :param server_ip (str)
        :param chassis_ip (str)
        :param user_name (str)
        :param user_pass (str)
        :param ixnetwork_type (str)
        :param host_name (str): Linux API server hostname 
        """
        self.ixnetwork_type = ixnetwork_type
        if self.ixnetwork_type == "windows":
            # Windows Chassis
            if chassis_ip:
                self.chassis_ip = chassis_ip
            else:
                self.server_ip = server_ip
                self.chassis_ip = None
            self.username = user_name
            self.password = user_pass
            self.hostname = 'platform'
        else:
            # Linux Chassis
            if chassis_ip:
                self.chassis_ip = chassis_ip
            else:
                self.server_ip = server_ip
                self.chassis_ip = None
            if host_name:
                self.hostname = host_name
            else:
                self.hostname = "ixnetworkweb"
            self.username = user_name
            self.password = user_pass
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = ''
        self.verbose = True
        self.poll_interval = 2
        self.timeout = 500
        self.authenticate()

    def get_ixos_uri(self):
        return 'https://%s/chassis/api/v2/ixos' % self.chassis_ip

    def get_chassis_uri(self):
        return 'https://%s' % self.chassis_ip 
    
    def get_licensing_uri(self):
        return 'https://%s/platform/api/v2/licensing' % self.chassis_ip

    def get_headers(self):
        # headers should at least contain these two
        return {
            "Content-Type": "application/json",
            'x-api-key': self.api_key
        }
    
    def get_host_id(self):
        chassis = self.get_chassis().data[0]
        logging.info(chassis['type'])
        server = self.get_license_servers().data[0]
        return server['id']

    def authenticate(self):
        try:
            logging.info('getting api key ...')
            payload = {
                'username': self.username,
                'password': self.password,
                'rememberMe': False
            }
            if self.chassis_ip:
                response = self.http_request(
                    'POST',
                    'https://%s/platform/api/v1/auth/session' % self.chassis_ip,
                    payload=payload
                    )
            else:
                if self.ixnetwork_type == "linux":
                    uri = 'https://{}/{}/api/v1/auth/session'.format(self.server_ip, self.hostname)
                else:
                    uri = 'https://{}/api/v1/auth/session'.format(self.server_ip)
                response = self.http_request('POST', uri, payload=payload)
            self.api_key = response.data['apiKey']
            logging.info('api key is %s' % self.api_key)
        except:
            raise

    def http_request(self, method, uri, payload=None):
        """
        wrapper over requests.requests to pretty print debug info
        and invoke async operation polling depending on HTTP status code
        """
        try:
            if not uri.startswith('http'):
                uri = self.get_ixos_uri() + uri
            
            if payload is not None:
                payload = json.dumps(payload, indent=2, sort_keys=True)
            headers = self.get_headers()
            # headers = json.load(headers)
            response = requests.request(
                method, uri, data=payload, headers=headers, verify=False
            )

            data = response.content.decode()
            try:
                data = json.loads(data) if data else None
            except:
                logging.info('Invalid/Non-JSON payload received: %s' % data)
                data = None
            if response.status_code == 202:
                return self.wait_for_async_operation(data)
            else:
                response.data = data
                return response
        except:
            raise

    def wait_for_async_operation(self, response_body):
        """
        method for handeling intermediate async operation results
        """
        try:
            logging.info('Polling for async operation ...')

            operation_status = response_body['state']
            start_time = int(time.time())
            while operation_status == 'IN_PROGRESS':
                response = self.http_request('GET', response_body['url'])
                response_body = response.data
                operation_status = response_body['state']                    

                if int(time.time() - start_time) > self.timeout:
                    raise IxRestException('timeout occured while polling for async operation')

                time.sleep(self.poll_interval)

            if operation_status == 'COMPLETED' or operation_status == 'SUCCESS':
                return response
            else:
                raise IxRestException('async operation failed')
        except:
            raise
        finally:
            logging.info('Completed async operation')

    def http_request_license(self, method, uri, payload=None):
        """
        wrapper over requests.requests to pretty print debug info
        and invoke async operation polling depending on HTTP status code
        """
        try:
            if not uri.startswith('http'):
                uri = self.get_ixos_uri() + uri
            if payload is not None:
                payload = json.dumps(payload, indent=2, sort_keys=True)
            headers = self.get_headers()

            response = requests.request(
                method, uri, data=payload, headers=headers, verify=False
            )
            data = response.content.decode()
            try:
                data = json.loads(data) if data else None
            except:
                logging.info('Invalid/Non-JSON payload received: %s' % data)
                data = None

            ### When license retrievel is in progress, Windows chassis returns code 200; 
            ### whereas Linux chassis returns code 202  
            if response.status_code == 202 or response.status_code == 200:
                return self.wait_for_async_operation_license(data)
            else:
                response.data = data
                return response
        except:
            raise

    def wait_for_async_operation_license(self, response_body):
        """
        method for handeling intermediate async operation results
        """
        try:
            logging.info('Polling for async operation ...')

            operation_status = response_body['state']
            start_time = int(time.time())
            while operation_status == 'IN_PROGRESS':
                uri = response_body['url']
                ### workaround for windows chassis
                if not uri.startswith('http'):
                    uri = self.get_chassis_uri() + uri
                response = self.http_request('GET', uri)
                response_body = response.data
                operation_status = response_body['state']                    

                if int(time.time() - start_time) > self.timeout:
                    raise IxRestException('timeout occured while polling for async operation')

                time.sleep(self.poll_interval)

            if operation_status == 'COMPLETED' or operation_status == 'SUCCESS':
                return response
            else:
                raise IxRestException('async operation failed')
        except:
            raise
        finally:
            logging.info('Completed async operation')

    def get_chassis(self):
        return self.http_request('GET', self.get_ixos_uri() + '/chassis')

    def get_cards(self):
        return self.http_request('GET', self.get_ixos_uri() + '/cards')

    def get_ports(self):
        return self.http_request('GET', self.get_ixos_uri() + '/ports')

    def get_services(self):
        return self.http_request('GET', self.get_ixos_uri() + '/services')

    def get_license_servers(self):
        return self.http_request('GET', self.get_licensing_uri() + '/servers')


    def take_ownership(self, resource_id):
        return self.http_request(
            'POST',
            self.get_ixos_uri() + '/ports/%d/operations/takeownership' % resource_id
        )

    def release_ownership(self, resource_id):
        return self.http_request(
            'POST',
            self.get_ixos_uri() + '/ports/%d/operations/releaseownership' % resource_id
        )

    def reboot_port(self, resource_id):
        return self.http_request(
            'POST',
            self.get_ixos_uri() + '/ports/%d/operations/reboot' % resource_id
        )

    def reset_port(self, resource_id):
        return self.http_request(
            'POST',
            self.get_ixos_uri() + '/ports/%d/operations/resetfactorydefaults' % resource_id
        )

    def hotswap_card(self, resource_id):
        return self.http_request(
            'POST',
            self.get_ixos_uri() + '/cards/%d/operations/hotswap' % resource_id
        )

    def cleanup_diskspace(self, resource_id):
            return self.http_request(
            'POST',
            self.get_ixos_uri() + '/chassis/%d/operations/cleanupdiskspace' % resource_id, payload={"daystokeep": 3}
        )

    def retrieve_chassistime(self, resource_id):
            return self.http_request(
            'POST',
            self.get_ixos_uri() + '/chassis/%d/operations/retrievechassistime' % resource_id
        )

    def retrieve_licenses(self, host_id):
            licenseQuery = self.http_request_license(
            'POST',
            self.get_licensing_uri() + '/servers/%d/operations/retrievelicenses' % host_id
            )
            resultUrl = licenseQuery.data['resultUrl']
            ### workaround for windows chassis
            if not resultUrl.startswith('http'):
                resultUrl = self.get_chassis_uri() + resultUrl
            import pdb;pdb.set_trace()
            response = self.http_request('GET', resultUrl)
            return response       
    
    def isLinuxChassis(self, type):
        if type == 'Ixia XGS12-HSL':
            return True
        elif type == 'Ixia XGS12':
            return False
        
    def retrieve_license_with_activationcode(self, active_code):
        if self.ixnetwork_type == "linux":
            host_uri = 'https://{}/{}/api/v2/licensing/servers'.format(self.server_ip, self.hostname)
            response = self.http_request('GET', host_uri)
            hostId = response.data[0]['id']
            uri = 'https://{}/api/v2/licensing/servers/{}/operations/retrieveactivationcodeinfo'.format(self.server_ip, hostId)        
        else:
            #Currently we dont have support on Windows because the license utility not integrated on the windows API server.
            host_uri = 'https://{}/api/v2/licensing/servers'.format(self.server_ip)
            response = self.http_request('GET', host_uri)
            hostId = response.data[0]['id']
            uri = 'https://{}/api/v2/licensing/servers/{}/operations/retrieveactivationcodeinfo'.format(self.server_ip, hostId)  
        licenseQuery = self.http_request_license(
        'POST', uri, payload={'activationCode': active_code}
        )
        resultUrl = licenseQuery.data['resultUrl']
        ### workaround for windows chassis
        if not resultUrl.startswith('http'):
            resultUrl = self.get_chassis_uri() + resultUrl
        
        response = self.http_request('GET', resultUrl)
        return response

    def csv_xlsx_retrieve_license(self, file_name, file_format="csv", activation_code=None):
        if self.chassis_ip:
            hostId = self.get_host_id()
            licenseResponse = self.retrieve_licenses(hostId) 
            licenseDetails = pd.DataFrame.from_dict(licenseResponse.json())  
        else:
            responeList = []
            for active_code in activation_code:
                licenseResponse = self.retrieve_license_with_activationcode(active_code)   
                responeList.append(licenseResponse.json())
            licenseDetails = pd.DataFrame.from_dict(responeList)
        if file_format == "csv":
            licenseDetails.to_csv(file_name + '.' + file_format)
        else:
            licenseDetails.to_excel(file_name + '.' + file_format)
        
