# Elevate

Aggregation ETL python microservice written in python 3.* with [chalice](https://chalice.readthedocs.io/). This service is deployed to [elevate.dperconti.com/incidents](https://elevate.dperconti.com/incidents)

## Setup & Installation
```bash
$ python3 --version
Python 3.7.3
$ python3 -m venv venv37
$ . venv37/bin/activate
$ pip install -r requirements.txt
$ cp .chalice/config.json.example .chalice/config.json
```

Once the `.chalice/config` has been copied over, add the user/pass env variables to connect to the respective APIs.

## Running Local
```bash
$ chalice local --port 9000
Restarting local dev server.
Serving on http://127.0.0.1:9000
```

## Response Format
```bash
{
    "4506": {
        "low": {
            "count": 0,
            "incidents": []
        }
        "medium": {
            "count": 3,
            "incidents": [
                {
                    "type": "executable"
                    "priority": "medium",
                    "machine_ip": "17.99.238.86",
                    "timestamp": 1500020421.9333,
                }
                ...
            ]
        }
        "high": {
            ...
        }
        ...
    },
    "9704": {
        "low": {
            "count": 10,
            "incidents": [
                {
                    ...
                },
                ...
            ]
        }
    },
    ...
}
```

## Todo
- Error logging and handling
- Performance enhancements


## Assumptions
There are a few endpoints that _do not_ return a user ID associated with the object. Because of this, the mappings between IP address and user ID [can be found here](https://github.com/dperconti/elevate/blob/master/chalicelib/elevate/api.py#L26-L44).

## Tasks

✅ Must query security incidents via HTTP
✅ Must group results by employee_id, and group incidents by priority level for each employee_id. Note: include the priority level even if the the incident count for that (employee, priority level) is 0 as demonstrated below in the example output (low priority is still included for employee 4506)
✅ Results should be sorted by incident timestamp (the incidents endpoint /incidents/<type> already returns incidents sorted by the timestamp - you can take advantage of this fact)
❌ Must return results within 2 seconds _Response time is currently ~6 seconds_
✅ You can write the API in whichever language and whichever libraries/framework you feel most comfortable with, and it should expose a single endpoint on port 9000
✅ GET /incidents - returns all types of incidents sorted by timestamp and grouped by employee and priority level for each employee.




