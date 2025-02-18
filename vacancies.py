from dotenv import load_dotenv
import os
import requests

load_dotenv()

class Vacancies:
    API_ENDPOINT = 'https://api.coresignal.com/cdapi/v1/professional_network/job/search/filter'
    API_KEY = os.getenv('CORESIGNAL_API_KEY')
    HEADERS = {"Authorization": f"Bearer {API_KEY}"}

    def __init__(self, job_title, country='', keyword_description='', city_or_state='', employment_type=''):
        self.job_title = job_title
        self.country = country
        self.keyword_description = keyword_description
        self.city_or_state = city_or_state
        self.employment_type = employment_type
        self.data = {
            "deleted": False, #false #to get only active vacancies
            "title": self.job_title,
            "keyword_description": self.keyword_description, #"python OR (software development)"
            "country": self.country,
            "location": self.city_or_state,
            "employment_type": self.employment_type #"Full-time OR Part-time"
        }


    def get_vacancies_id_list(self):

        """
        Makes the API request and gets list of jobs ID's. Cut the list if it contains more than 3 items.
        :return: List of ID's of job vacancies
        """
        try:
            response = requests.post(Vacancies.API_ENDPOINT, headers=Vacancies.HEADERS, json=self.data)
            parsed_response = response.json()
            #return only 3 vacancies because we have limited amount of API requests
            if len(parsed_response) > 3:
                parsed_response = parsed_response[0:3]
            return parsed_response
        except requests.exceptions.MissingSchema:
            print('Impossible to reach the endpoint')
        except requests.exceptions.JSONDecodeError:
            print('Impossible to parse json')
        except Exception as e:
            print(f"Such error occurred: {e}")


    def get_vacancies_info_list(vacancies_list: list):

        """
        Makes the API request for each vacancy ID in the obtained list and get the information about each vacancy.
        Formats the obtained information.
        :return: List of dictionaries with vacancies info
        """

        try:
            if not isinstance(vacancies_list, list):
                raise Exception('Wrong format of the vacancies list')
            vacancies_info_list = []
            for vacancy_id in vacancies_list:
                get_endpoint = f"https://api.coresignal.com/cdapi/v1/professional_network/job/collect/{vacancy_id}"
                response = requests.get(get_endpoint, headers=Vacancies.HEADERS)
                parsed_response = response.json()
                job_title = parsed_response['title']
                location = parsed_response['location']
                url = parsed_response['url']
                company_name = parsed_response['company_name']
                description = parsed_response['description'].split('.')[0:3]
                description = ''.join(description) + '...'
                seniority = parsed_response['seniority']
                employment_type = parsed_response['employment_type']
                applicants_count = parsed_response['applicants_count']
                vacancy_info = {
                    'title': job_title,
                    'location': location,
                    'url': url,
                    'company_name': company_name,
                    'description': description,
                    'seniority': seniority,
                    'employment_type': employment_type,
                    'applicants_count': applicants_count
                }
                vacancies_info_list.append(vacancy_info)
            if len(vacancies_info_list) == 0 or vacancies_info_list == [{'detail': 'Not Found'}]:
                return 'Sorry, nothing was found.'
            return vacancies_info_list
        except requests.exceptions.MissingSchema:
            print('Impossible to reach the endpoint')
        except requests.exceptions.JSONDecodeError:
            print('Impossible to parse json')
        except Exception as e:
            print(f"Such error occurred: {e}")
