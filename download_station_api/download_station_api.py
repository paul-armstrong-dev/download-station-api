"""Main module."""
import time
from typing import Dict

import requests
from loguru import logger

from .utils.auth_error import AuthError
from .utils.api_endpoint_details import nas_api_endpoint_details

# Class written to interact with the Synology download station API
# api docs stored here:
# https://global.download.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf


# Here to quiet "code smells" / neaten up the code a bit
PROBLEM_ADDING_DOWNLOAD_LOG = "Problem adding download task"
ERROR_LOG = ""


class DownloadStationAPI:
    def __init__(self,
                 user_name: str,
                 password: str,
                 nas_ip: str,
                 api_port: str = "5000",
                 api_endpoint: str = "webapi"):
        """

            :param user_name: Local Synology username
            :param password: Local synology password
            :param nas_ip: Synology IP address which hosts the download station instance
            :param api_endpoint: Optional, defaults to webapi, should only be changed if a separate endpoint has been configured
            :param api_port: Optional, defaults to 5000
        """
        self.class_name = type(self).__name__
        logger.info(f"{self.class_name} initialised")

        self.user_name = user_name
        self.password = password
        self.nas_ip = nas_ip
        self.api_endpoint = api_endpoint
        self.api_port = api_port
        self.nas_address = f"http://{self.nas_ip}:{api_port}/{api_endpoint}"
        self.session_id = self.authenticate(session='DownloadStation',
                                            auth_format='cookie',
                                            method='login',
                                            version=2)

    def _get_api_data(self, api_endpoint: str, params: Dict, return_json: bool = True):
        """

        :param api_endpoint: self-explanatory
        :param params: Request params be passed through to API
        :param return_json: Specify whether to return json/dict or the entire requests.response
        :return: API data in specified format
        :rtype: Either dict or raw response, depending on last parameter
        """

        endpoint_info = nas_api_endpoint_details.get(api_endpoint)

        api_endpoint = endpoint_info.get("api_endpoint")
        api_path = endpoint_info.get("path")

        api_url = f'{self.nas_address}/{api_path}?api={api_endpoint}'
        response = requests.get(api_url, params=params)

        if return_json:
            return response.json()
        else:
            return response

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                'Problem in {class_name}'.format(class_name=self.class_name))
            logger.error(exc_type)
            logger.error(exc_val)
            exit(1)
        logger.info('{class_name} exited successfully'.format(
            class_name=self.class_name))

        # Step 4 - Logout of API session
        logout_params = {
            'version': 1,
            'method' : 'logout',
            'session': 'DownloadStation'
        }

        api_path = nas_api_endpoint_details['API_Auth']['path']
        api_endpoint = nas_api_endpoint_details['API_Auth']['api_endpoint']

        api_url = f'{self.nas_address}/{api_path}?api={api_endpoint}'
        response = requests.get(api_url, params=logout_params)
        if response.status_code == 200:
            logger.info('API session successfully closed')
        else:
            logger.error('Problem with closing API sessions')
        return self

    def authenticate(self, session: str, auth_format: str, method: str, version: int) -> str:
        """
            See init for example usage

            :param session: Authentication session type.
            :param auth_format: Authentication format
            :param method: Authentication method
            :param version: API version to address
        """
        authentication_params = {
            'session': session,
            'format' : auth_format,
            'method' : method,
            'version': version,
            'account': self.user_name,
            'passwd' : self.password
        }
        # Authorization, returns SID
        data = self._get_api_data("API_Auth", authentication_params)

        if data['success']:
            # If successfully authenticated use
            # the SID in the subsequent requests
            logger.success("successfully authenticated")
            session_id = data['data']['sid']
            return session_id
        else:
            logger.error(data)
            raise AuthError('Authentication unsuccessful')

    def search(self,
               search_term: str,
               wait_time: int = 30,
               quality_to_search: str = '720p') -> object:
        """

        * Uses any configured search locations configured for the download station to search
        * Essentially the same as typing in the search bar there

        :param search_term: Thing to search for
        :param wait_time: Time to wait for the search to complete.
        :param quality_to_search: Video quality to search for.
        :return:
        :rtype:
        """
        # Start search and get taskID

        search_params = {
            'version': 1,
            'method' : 'start',
            'keyword': search_term,
            'module' : 'enabled',
            '_sid'   : self.session_id
        }
        response = self._get_api_data("DS_BT_Search", search_params, return_json=False)

        data = response.json()
        search_task_id = data['data']['taskid']

        if response.status_code == 200:
            logger.info(f"Starting {wait_time} second search for {search_term}")
            time.sleep(wait_time)

            search_params = {
                'sort_by'       : 'seeds',
                'sort_direction': 'desc',
                'version'       : 1,
                'method'        : 'list',
                'filter_title'  : quality_to_search,
                'taskid'        : search_task_id,
                '_sid'          : self.session_id
            }
            response = self._get_api_data("DS_BT_Search", search_params, return_json=False)
            data = response.json()
            logger.info(f"Finished search for {search_term}")
            logger.debug(data)

            return data['data']
        else:
            logger.error('Problem with search')
            return None

    def check_if_search_is_done(self,
                                search_task_id: str,
                                quality_to_search: str):
        """

        :param search_task_id:
        :param quality_to_search:
        :type quality_to_search:
        :return:
        """
        search_params = {
            'sort_by'       : 'seeds',
            'sort_direction': 'desc',
            'version'       : 1,
            'method'        : 'list',
            'filter_title'  : quality_to_search,
            'taskid'        : search_task_id,
            '_sid'          : self.session_id
        }

        data = self._get_api_data("DS_BT_Search", search_params)
        logger.debug(data)
        if data["data"]["finished"] is False:
            return data["data"]["finished"]
        else:
            return data["data"]

    def bt_search_with_wait(self,
                            search_term: str,
                            default_search_quality: str = "720p"):
        """

                :param search_term:
                :param default_search_quality:
                :return:
                :rtype:
        """

        # Start search and get taskID
        logger.info(f"Searching for {search_term}")

        search_params = {
            'version': 1,
            'method' : 'start',
            'keyword': search_term,
            'module' : 'enabled',
            '_sid'   : self.session_id
        }
        data = self._get_api_data("DS_BT_Search", search_params)
        logger.debug(data)

        search_task_id = data['data']['taskid']

        logger.info("Small wait")
        time.sleep(2)

        while self.check_if_search_is_done(search_task_id,
                                           quality_to_search=default_search_quality) is False:
            logger.info("Search not complete, waiting 5 seconds")
            time.sleep(5)

        # then Returns data using same function
        return self.check_if_search_is_done(search_task_id,
                                            quality_to_search=default_search_quality)

    def get_individual_download_info(self, download_task_id: str) -> Dict:
        """
        :param download_task_id:
        :return:
        :rtype:
        """
        logger.info('Getting individual info')

        get_info_params = {
            'version'   : 1,
            'method'    : 'getinfo',
            'additional': 'detail,file',
            # ! Sid must always be last
            'id'        : download_task_id,
            '_sid'      : self.session_id
        }

        data = self._get_api_data("DS_Task", get_info_params)

        if data['success'] is True:
            logger.info('Download info retrieved')
            return data['data']
        else:
            logger.error(PROBLEM_ADDING_DOWNLOAD_LOG)
            logger.error(data)

    def get_download_info(self) -> Dict:
        """

        Retrieves a list of current downloads

        :return: Dict containing a list of current downloads along with metadata
        :rtype: Dict
        """
        logger.info('Getting current download info')
        get_info_params = {
            'version'   : 1,
            'method'    : 'list',
            'additional': 'detail,file',
            # ! Sid must always be last
            '_sid'      : self.session_id
        }
        data = self._get_api_data("DS_Task", get_info_params)

        if data['success'] is True:
            logger.info('Download info retrieved')
            return data['data']
        else:
            logger.error(PROBLEM_ADDING_DOWNLOAD_LOG)
            logger.error(data)

    # Defaulting to series at the moment
    def add_download_task(self, url: str, destination: str = '') -> bool:
        """
            :param url: Magnet download URL
            :param destination: Relative synology URL. If left blank will take the default of the synology download station
            :return: True or false based on whether or the the download was successfully added
            :rtype: bool
        """
        logger.info('Adding download task')

        search_params = {
            'version'    : 2,
            'method'     : 'create',
            'uri'        : url,
            'destination': destination,
            # ! Sid must always be last
            '_sid'       : self.session_id
        }

        data = self._get_api_data("DS_Task", search_params)

        if data['success'] is True:
            logger.info('Download task successfully added')
            return True
        else:
            logger.error(PROBLEM_ADDING_DOWNLOAD_LOG)
            logger.error(data)
            return False

    def resume_download_task(self, download_task_id: object) -> bool:
        """
        :return:
        :rtype:
        :rtype: object
        :param download_task_id: Synology task ID, retrieved when getting the download info
        :return:
        """
        resume_params = {
            'version': 1,
            'method' : 'resume',
            'id'     : download_task_id,
            # ! Sid must always be last
            '_sid'   : self.session_id
        }

        data = self._get_api_data("DS_Task", resume_params)
        if data['success'] is True:
            logger.info('Download resumed')
            return True
        else:
            logger.error('Problem resuming download task')
            logger.error(data)
            return False

    def remove_download_task(self, download_task_id: object) -> bool:
        """

        :return: True if removed successfully
        :rtype: bool
        :param download_task_id: Synology task ID, retrieved when getting the download info
        """
        logger.info("Removing {}".format(download_task_id))
        delete_params = {
            'version': 1,
            'method' : 'delete',
            'id'     : download_task_id,
            # ! Sid must always be last
            '_sid'   : self.session_id
        }

        data = self._get_api_data("DS_Task", delete_params)
        if data['success'] is True:
            logger.info('Download removed')
            return True
        else:
            logger.error('Problem removing download')
            logger.error(data)
            return False

    def correct_finished_downloads(self, download_task_id: str) -> bool:
        """

        Simple function written for finished downloads, in the case that the download has already completed rather
        resume it so we can get more info or remove it if the file is no longer there

        :param download_task_id:
        :return: True if corrected successfully
        :rtype: bool
        """
        old_status = 'finished'
        new_status = old_status
        while new_status == old_status:
            self.resume_download_task(download_task_id=download_task_id)
            time.sleep(5)
            new_status = self.get_individual_download_info(
                download_task_id=download_task_id)['tasks'][0]['status']
            logger.info(new_status)
            if new_status == 'seeding':
                logger.info('Successfully resumed')
            if new_status == 'downloading':
                logger.info('Incorrectly resumed')
                self.remove_download_task(download_task_id=download_task_id)
        return True

if __name__ == '__main__':
    # Example values
    ds = DownloadStationAPI(user_name="<user_name>", password="<password>", nas_ip="<ipaddress>")
