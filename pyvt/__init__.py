import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

class Timetable:
    def __init__(self):
        self.url = 'https://apps.es.vt.edu/ssb/HZSKVTSC.P_ProcRequest'
        self.sleep_time = 1
        self.base_request = {  # base required request data
            'BTN_PRESSED': 'FIND class sections',
            'CAMPUS': '0',  # default to Blacksburg campus
            'SCHDTYPE': '%'  # default to all schedule types
        }
        self.data_keys = ['crn', 'code', 'name', 'lecture_type', 'modality', 'credits', 'capacity', 'instructor', 'days', 'start_time', 'end_time', 'location', 'exam_type']

    @property
    def _default_term_year(self):
        term_months = [1, 6, 7, 9]  # Spring, Summer I, Summer II, Fall
        current_year = datetime.today().year
        current_month = datetime.today().month
        term_month = max(key for key in term_months if key <= current_month)
        return '%d%s' % (current_year, str(term_month).zfill(2))

    def refined_lookup(self, crn_code=None, subject_code=None, class_number=None, cle_code=None,
                       term_year=None, open_only=True):
        request_data = self.base_request.copy()
        request_data['TERMYEAR'] = term_year if term_year is not None else self._default_term_year

        if crn_code is not None:
            if len(crn_code) < 3:
                raise ValueError('Invalid CRN: must be longer than 3 characters')
            request_data['crn'] = crn_code

        if subject_code is not None:
            request_data['subj_code'] = subject_code

        if class_number is not None:
            if len(class_number) != 4:
                raise ValueError('Invalid Subject Number: must be 4 characters')
            request_data['CRSE_NUMBER'] = class_number

        if subject_code is None and class_number is not None:
            raise ValueError('A subject code must be supplied with a class number')

        request_data['CORE_CODE'] = 'AR%' if cle_code is None else cle_code
        request_data['open_only'] = 'on' if open_only else ''
        request_data['sess_code'] = '%'

        req = self._make_request(request_data)
        # save req to file
        with open('req.html', 'w') as f:
            f.write(str(req))
        sections = self._parse_table(req)
        return None if sections is None or len(sections) == 0 else sections

    def subject_lookup(self, subject_code, term_year=None, open_only=True):
        return self.refined_lookup(subject_code=subject_code, term_year=term_year, open_only=open_only)

    def _make_request(self, request_data):
        print(f'Requesting data from {self.url}:\n{request_data}')
        # r = requests.post(self.url, data=request_data, headers=self.headers)
        r = requests.post(self.url, data=request_data)
        if r.status_code != 200:
            self.sleep_time *= 2
            raise TimetableError('The VT Timetable is down or the request was bad. Status Code was: %d'
                                 % r.status_code, self.sleep_time)
        self.sleep_time = 1

        return BeautifulSoup(r.content, 'html.parser')

    def _parse_row(self, row):
        entries = [entry.text.replace('\n', '').replace('-', ' ').strip() for entry in row.find_all('td')]
        return Section(**dict(zip(self.data_keys, entries)))

    def _parse_table(self, html):
        table = html.find('table', attrs={'class': 'dataentrytable'})
        if table is None:
            return None
        rows = [row for row in table.find_all('tr') if row.attrs == {}]
        sections = [self._parse_row(c) for c in rows]
        return sections


class TimetableError(Exception):
    def __init__(self, message, sleep_time):
        super(TimetableError, self).__init__(message)
        self.sleep_time = sleep_time


class Section:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def tuple_str(tup):
        return str(tup).replace("'", "")
    
    def print_info(self):
        print(f'Course: {self.name} - CRN: ({self.crn})')
        for key in self.__dict__:
            if key in ['name', 'crn']:
                continue
            print(f'\t{key}: {self.__dict__[key]}')
        print()

    def __str__(self):
        name = getattr(self, 'name', None)
        crn = getattr(self, 'crn', None)
        days = getattr(self, 'days', None)
        start_time = getattr(self, 'start_time', None)
        end_time = getattr(self, 'end_time', None)
        
        print(f'name: {name}, crn: {crn}, days: {days}, start_time: {start_time}, end_time: {end_time}')
        
        return '%s (%s) on %s at %s' % (name, crn, days, Section.tuple_str((start_time, end_time)))

    def get_info(self):
        return self.__dict__
