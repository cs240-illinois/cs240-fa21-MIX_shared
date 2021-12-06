from flask import Flask, render_template, request, jsonify
import requests
from microservice import Microservice

import json
from datetime import datetime

app = Flask(__name__)

connected_apps = set()
processed = {}
cache = {}


# Route for "/" (frontend):
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/microservice', methods=['PUT'])
def add_microservice():
    # Verify all required keys are present in JSON:
    required_keys = ['port', 'ip', 'name', 'creator', 'tile']
    for required_key in required_keys:
        if required_key not in request.json:
            return f'Required key {required_key} not present in payload JSON.', 400

    # Add the microservice:
    dependency_list = convert_dependencies_to_objects(request.json['dependencies'])
    m = Microservice(
        request.json['ip'] + ':' + request.json['port'],
        dependency_list,
        request.json['name'],
        request.json['creator'],
        request.json['tile'],
    )
    print('connection received from: ' + m.ip)
    connected_apps.add(m)

    return 'Success', 200


def convert_dependencies_to_objects(dependencies):
    dp_list = []
    for x in dependencies:
        # recursively fetch dependency lists where necessary
        if list(x['dependencies']) != list():
            dp_list.append(Microservice(x['ip'] + ':' + x['port'], convert_dependencies_to_objects(x['dependencies'])))
        else:
            dp_list.append(Microservice(x['ip'] + ':' + x['port'], []))

    return dp_list


@app.route('/microservice', methods=['DELETE'])
def remove_microservice():
    print(f'delete request received from: {request.host}')
    previous_len = len(connected_apps)
    j = request.json

    if 'ip' not in j or 'port' not in j:
        return 'Invalid Input', 400

    ip = j['ip'] + ':' + j['port']
    m = Microservice(ip, [])

    connected_apps.discard(m)
    if len(connected_apps) == previous_len:
        return 'Not Found', 404

    return 'Success', 200


# Route for "/MIX" (middleware):
@app.route('/MIX', methods=["POST"])
def POST_MIX():
    global connected_apps
    # process form data
    location = request.form['location']
    s = location.split(',')
    lat = float(s[0])
    lon = float(s[1])

    if abs(lat) > 90:
        return 'Invalid latitude', 400

    if abs(lon) > 180:
        return 'Invalid longitude', 400

    # clear list of processed requests from connected apps
    processed.clear()

    # aggregate JSON from all IMs
    r = []
    app_list = connected_apps.copy()
    for app in app_list:
        # create a response with the metadata about the IM service:
        j = {
            '_metadata': {
                'name': app.name,
                'creator': app.creator,
                'tile': app.tile,
            }
        }

        # add the IM response:
        if cache_hit((lat, lon), app):
            j.update(cache[(lat, lon)][app.ip][0])
        else:
            j.update(process_request(app, lat, lon))

        r.append(j)

    return jsonify(r), 200


def process_request(service: Microservice, lat: float, lon: float) -> dict:
    latlon_data = {'latitude': lat, 'longitude': lon}
    # if we've already processed an IM, we're finished
    if service.ip in processed:
        return processed[service.ip]

    if len(service.dependencies) == 0:
        # send a request to each service
        return make_im_request(service, latlon_data, lat, lon)
    else:
        # aggregate all dependency data and send as a request to our IM
        dependency_json = get_dependency_data(service, lat, lon)
        dependency_json.update(latlon_data)
        return make_im_request(service, dependency_json, lat, lon)


def get_dependency_data(service: Microservice, lat: float, lon: float) -> dict:
    j = {}
    for dependency in service.dependencies:
        # handle dependencies which have their own dependencies recursively
        if len(dependency.dependencies) > 0:
            for dd in dependency.dependencies:
                j.update(get_dependency_data(dd, lat, lon))

        else:
            # if we've already made a request to this IM, just fetch from our processed requests dict
            if dependency.ip in processed:
                j.update(processed[dependency.ip])
            else:
                # make new request to IM
                latlon_data = {'latitude': lat, 'longitude': lon}
                j.update(make_im_request(dependency, latlon_data, lat, lon))

    return j


def make_im_request(service: Microservice, j: dict, lat: float, lon: float) -> dict:
    try:
        r = requests.get(service.ip, json=j)
    except requests.exceptions.RequestException:
        print(f'app {service.name} at address {service.ip} not connecting. removed from MIX!')
        connected_apps.discard(service)
        return {}
    if r.status_code >= 400:
        print(f'service {service.ip} returned error code {str(r.status_code)}')
        return {}

    add_entry_to_cache((lat, lon), service, r)
    processed[service.ip] = r.json()
    return r.json()


def parse_cache_header(header: str) -> float:
    return float(header.split('=')[1])


def add_entry_to_cache(latlon: tuple, service: Microservice, response) -> None:
    # set max_age for a service if it has not been set already
    if service.max_age == 0:
        service.max_age = parse_cache_header(response.headers['Cache-Control'])

    # enter the service response json into our cache
    if latlon not in cache:
        cache[latlon] = {service.ip: (response.json(), datetime.now())}
    else:
        cache[latlon][service.ip] = (response.json(), datetime.now())


def cache_hit(latlong: tuple, service: Microservice) -> bool:
    if service.max_age == 0 or latlong not in cache or service.ip not in cache.get(latlong):
        print('cache miss! entry not in cache')
        return False

    curr_time = datetime.now()
    timediff = curr_time - cache[latlong][service.ip][1]

    if timediff.total_seconds() < service.max_age:
        print('cache hit!')
        return True

    print('cache miss! exceeded max_age')
    return False
