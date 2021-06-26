"""Main module."""
import time
import requests
from loguru import logger

# Class written to interact with the Synology download station API
# api docs stored here:
# https://global.download.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf


class AuthError(Exception): pass


nas_api_endpoint_details = {
    'API_Info'    : {'maxVersion'  : 1, 'minVersion': 1, 'path': 'query.cgi',
                     'api_endpoint': 'SYNO.API.Info'},
    'API_Auth'    : {'maxVersion'  : 6, 'minVersion': 1, 'path': 'auth.cgi',
                     'api_endpoint': 'SYNO.API.Auth'},
    'DS_Info'     : {'maxVersion'  : 2, 'minVersion': 1,
                     'path'        : 'DownloadStation/info.cgi',
                     'api_endpoint': 'SYNO.DownloadStation.Info'},
    'DS_BT_Search': {'maxVersion'  : 1, 'minVersion': 1,
                     'path'        : 'DownloadStation/btsearch.cgi',
                     'api_endpoint': 'SYNO.DownloadStation.BTSearch'},
    'DS_Task'     : {'maxVersion'  : 3, 'minVersion': 1,
                     'path'        : 'DownloadStation/task.cgi',
                     'api_endpoint': 'SYNO.DownloadStation.Task'}
}

"""

From Synology docs
    5 Basic elements of requests to their APIS
         API name: Name of the API requested
         version: Version of the API requested
         path: cgi path of the API. The path information can be retrieved by
            requesting SYNO.API.Info
         method: Method requested
         _sid: Authorized session ID. Each API request should pass a sid value
            via either HTTP

GET
/webapi/<CGI_PATH>?api=<API_NAME>&version=<VERSION>&method=<METHOD>[&<PARAMS>][&_sid=<SID>]
"""
# Here to quiet "code smells" / neaten up the code a bit
PROBLEM_ADDING_DOWNLOAD_LOG="Problem adding download task"
ERROR_LOG=""

class DownloadStationAPI:

    def __init__(self, user_name, password, nas_ip, api_port="5000", api_endpoint="webapi"):
        """

            :param user_name:
            :param password:
            :param nas_address:
            :param api_endpoint:
            :param api_port:
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
                                            format='cookie',
                                            method='login',
                                            version=2)

    def authenticate(self, session, format, method, version):
        """
            ADD DOCS
        """
        authentication_params = {
            'session': session,
            'format' : format,
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

    def _get_api_data(self, api_endpoint, params=None, return_json=True):
        """

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

    def bt_search_for_show(self,
                           search_term,
                           wait_time=30,
                           quality_to_search='720p',
                           retry_without_filters=False):
        """
            GET
                taskid  Task ID
                offset  Optional.
                Beginning task on the requested record. Default to “0”.
                    limit   Optional. Number of records requested: “-1”
                Beans to list all tasks. Default to “-1”.
                    sort_by Optional.
                Possible value is title, size, date, peers, provider, seeds
                    or leechs. Default to ‘title’
                sort_direction Possible value is desc or asc
                filter_category Optional. Filter the records by the category
                    using Category ID returned
                    by getCategory function. Default to ‘’
                filter_title Optional. Filter the records by the title using
                    this parameter. Default to ‘’
        :param search_term:
        :param wait_time:
        :param quality_to_search:
        :return:
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
                                search_task_id,
                                quality_to_search):

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

    def bt_search_with_wait(self, search_term, default_search_quality="720p"):
        """
                    GET
                        taskid  Task ID
                        offset  Optional.
                        Beginning task on the requested record. Default to “0”.
                            limit   Optional. Number of records requested: “-1”
                        Beans to list all tasks. Default to “-1”.
                            sort_by Optional.
                        Possible value is title, size, date, peers, provider, seeds
                            or leechs. Default to ‘title’
                        sort_direction Possible value is desc or asc
                        filter_category Optional. Filter the records by the category
                            using Category ID returned
                            by getCategory function. Default to ‘’
                        filter_title Optional. Filter the records by the title using
                            this parameter. Default to ‘’
                :param search_term:
                :param default_search_quality:
                :return:
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

    def get_individual_download_info(self, download_task_id):
        """
            GET /webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1&method=list
        :return:
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
            return False

    def get_download_info(self):
        """
            GET /webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1&method=list
        :return:
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
            return False

    # Defaulting to series at the moment
    def add_download_task(self, url, destination='/AutomaticDownloads/Series'):
        """
        /AutomaticDownloads/Series/
        /var/services/video/Download/
        POST /webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1
        &method=create&uri=ftps://192.0.0.1:21/test/test.zip&username=admin&password=123
            :return: True or false based on successful add
        """
        logger.info('Adding download task')

        search_params = {
            'version': 2,
            'method' : 'create',
            'uri'    : url,
            'destination': destination,
            # ! Sid must always be last
            '_sid'   : self.session_id
        }

        data = self._get_api_data("DS_Task", search_params)

        if data['success'] is True:
            logger.info('Download task successfully added')
            return True
        else:
            logger.error(PROBLEM_ADDING_DOWNLOAD_LOG)
            logger.error(data)
            return False

    def resume_download_task(self, download_task_id):
        """
        GET /webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1&method=resume&id=dbid_001,dbid_002
        Response
            id Task IDs 1 and later error Action result. Error=0 for success.

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

    def remove_download_task(self, download_task_id):
        """
        GET /webapi/DownloadStation/task.cgi?api=SYNO.DownloadStation.Task&version=1&method=delete&id=
        Response
            id Task IDs 1 and later error Action result. Error=0 for success.

        :param download_task_id: Synology task ID, retrieved when getting the download info
        :return:
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

    def correct_finished_downloads(self, download_task_id):
        """
            Simple function written for finished downloads,
            In the case that the download has already completed rather resume it so we can get more info
            Or remove it if the file is no longer there
        :param download_task_id:
        :return:
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
