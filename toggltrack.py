# Nov24, 2021, ms
# toggltrack.py

# functions for toggl API

import adafruit_requests as requests
import json


def startTimeEntry(desc, pid, wid, auth):
    """
    desc: description for the entry
    pid: project id
    wid: workspace id
    """

    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth
    }

    data = '{"time_entry":{"description":"' + desc + '",'
    data += '"pid":' + pid + ','
    data += '"wid":' + wid + ','
    data += '"created_with":"curl"}' + '}'
    print('[debug] header')
    print(headers)
    print('[debug] data')
    print(data)

    uri = 'https://api.track.toggl.com/api/v8/time_entries/start'
    response = requests.post(uri, headers=headers, data=data)
    print('[debug] response.status_code')
    print(response.status_code)
    print('[debug] response.text')
    print(response.text)
    print()
    py_dict = json.loads(response.text)
    entry_id = py_dict['data']['id']
    print('[debug] time entry id:', entry_id)

    return entry_id


def stopTimeEntry(entry_id, auth):
    """
    stop is easier.  just include entry_id in the uri
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': auth,
        'Content-length': "0"
    }

    uri = 'https://api.track.toggl.com/api/v8/time_entries/'
    uri += str(entry_id) + '/stop'

    print()
    print('[debug] header')
    print(headers)
    print('[debug] uri')
    print(uri)
    response = requests.put(uri, headers=headers)

    print('[debug] response.text')
    print(response.text)
    print()


if __name__ == '__main__':
    pass
