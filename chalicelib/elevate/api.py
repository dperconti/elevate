from multiprocessing import Process, Pipe
import time
from chalicelib.elevate.config import ips
from itertools import groupby
import operator
import re
import requests
from multiprocessing import Process, Pipe
import os


class ENDPOINTS():
    DENIAL = "https://incident-api.use1stag.elevatesecurity.io/incidents/denial"
    INTRUSION = "https://incident-api.use1stag.elevatesecurity.io/incidents/intrusion"
    EXECUTABLE = "https://incident-api.use1stag.elevatesecurity.io/incidents/executable"
    MISUSE = "https://incident-api.use1stag.elevatesecurity.io/incidents/misuse"
    UNAUTHORIZED = "https://incident-api.use1stag.elevatesecurity.io/incidents/unauthorized"
    PROBING = "https://incident-api.use1stag.elevatesecurity.io/incidents/probing"
    OTHER = "https://incident-api.use1stag.elevatesecurity.io/incidents/other"


def convert_ips(incidents):
    """
    Some incidents have IP addresses instead of employee ID - mapping back
    """
    for incident in incidents:
        if 'employee_id' not in incident:
            if incident.get('internal_ip'):
                incident['employee_id'] = ips.get(incident.get('internal_ip'))
            if incident.get('machine_ip'):
                incident['employee_id'] = ips.get(incident.get('machine_ip'))
            if incident.get('ip'):
                incident['employee_id'] = ips.get(incident.get('ip'))
            if incident.get('identifier'):
                is_ip_address = re.match(
                    r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", str(incident.get('identifier')))
                if is_ip_address:
                    incident['employee_id'] = ips.get(
                        incident.get('identifier'))
                else:
                    incident['employee_id'] = incident.get('identifier')
            if incident.get('reported_by'):
                incident['employee_id'] = incident.get('reported_by')
    return incidents


def group_by_employee(flat_incidents):
    """
    Group the incidents by employee
    """
    incidents = {}
    for employee_id, employee_incident in groupby(flat_incidents, key=lambda x: x.get('employee_id')):
        if employee_id in incidents:
            incidents[employee_id] += list(employee_incident)
        else:
            incidents[employee_id] = list(employee_incident)
    return incidents


def group_by_incidents(incidents):
    """
    Group the incidents by the priority
    """
    return_incidents = {}

    for employee_id, employee_incidents in incidents.items():
        for incident_priority, grouped_priority in groupby(employee_incidents, key=lambda x: x.get('priority')):
            if employee_id not in return_incidents:
                return_incidents[employee_id] = {
                    'low': {
                        "count": 0,
                        "incidents": []
                    },
                    'medium': {
                        "count": 0,
                        "incidents": []
                    },
                    'high': {
                        "count": 0,
                        "incidents": []
                    },
                    'critical': {
                        "count": 0,
                        "incidents": []
                    }
                }
            return_incidents[employee_id][incident_priority]['incidents'] += list(
                grouped_priority)
        for priority in return_incidents[employee_id]:
            return_incidents[employee_id][priority]['count'] = len(
                return_incidents[employee_id][priority]['incidents'])
            return_incidents[employee_id][priority]['incidents'].sort(
                key=operator.itemgetter('timestamp'))
    return return_incidents


class IncidentsParallel(object):
    def __init__(self, sites=None):
        self.sites = sites

    def get_data(self, site, conn):
        """
        Method responsible for obtaining and updating incident types
        """
        r = requests.get(
            site,
            auth=(
                os.environ.get("ELEVATE_AUTH_USER"),
                os.environ.get("ELEVATE_AUTH_PASS")
            )
        )
        response = r.json().get('results')
        if site == ENDPOINTS.DENIAL:
            for incident in response:
                incident['type'] = 'denial'
        if site == ENDPOINTS.INTRUSION:
            for incident in response:
                incident['type'] = 'intrusion'
        if site == ENDPOINTS.EXECUTABLE:
            for incident in response:
                incident['type'] = 'executable'
        if site == ENDPOINTS.MISUSE:
            for incident in response:
                incident['type'] = 'misuse'
        if site == ENDPOINTS.UNAUTHORIZED:
            for incident in response:
                incident['type'] = 'unauthorized'
        if site == ENDPOINTS.PROBING:
            for incident in response:
                incident['type'] = 'probing'
        if site == ENDPOINTS.OTHER:
            for incident in response:
                incident['type'] = 'other'
        conn.send(response)
        conn.close()

    def total_incidents(self):
        """
        Manages the multi-threading connections to retreive the data
        """
        sites = [
            ENDPOINTS.DENIAL,
            ENDPOINTS.INTRUSION,
            ENDPOINTS.EXECUTABLE,
            ENDPOINTS.MISUSE,
            ENDPOINTS.UNAUTHORIZED,
            ENDPOINTS.PROBING,
            ENDPOINTS.OTHER
        ]

        processes = []

        parent_connections = []

        for site in sites:
            parent_conn, child_conn = Pipe()
            parent_connections.append(parent_conn)

            process = Process(
                target=self.get_data,
                args=(site, child_conn,)
            )
            processes.append(process)

        for process in processes:
            process.start()

        instances_total = []
        for parent_connection in parent_connections:
            instances_total += parent_connection.recv()

        for process in processes:
            process.join()

        instances_total = convert_ips(instances_total)
        instances_total = group_by_employee(instances_total)
        instances_total = group_by_incidents(instances_total)

        return instances_total


def lambda_handler():
    """
    Entry function to obtain all data
    """
    incidents = IncidentsParallel()
    total = incidents.total_incidents()
    return total
