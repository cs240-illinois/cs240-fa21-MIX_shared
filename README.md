# Project MIX: API Documentation

*This documentation was first created by Jackson Kennel, with additions from Kevin Chen's design, and further modifications for CS 240's final project.*


## Adding a Microservice:

In order to add a microservice to MIX, the microservice in question must make a `PUT` request to the /microservice endpoint. The `PUT` request must send JSON adhering to the following schema:

```
{
    'port' : 'HOST PORT',
    'ip' : 'HOST PROTOCOL and IP',

    'name': 'Sunrise Time',
    'creator': 'Your Name',
    'tile': 'For use on the front-end display (ex: Sunrise Time ☀️)',

    'dependencies' : [
        {
            'name' : 'Another IM',
            'creator' : 'Your Name'
        },
        {
            'port' : 'HOST PORT',
            'ip' : 'HOST PROTOCOL and IP'
        }
    ]
}
```

On the first request, MIX will search the list of connected IMs to match the specified dependencies.

The accepted formats are (in order of match priority):
- `name` and `creator`
- `ip` and `port`

To track the IP of the microservice, MIX will fetch the IP from the request.

To handle multiple IMs, MIX maintains a running list of all connected IMs. MIX will add all dependencies as if they were independent IMs. For dependency handling, see below.

## Removing a Microservice:

To remove a microservice from MIX, the microservice must make a `DELETE` request to the /microservice endpoint. The `DELETE` request must send JSON adhering to the following schema:

```
{ 
    'port' : 'HOST PORT'
    'ip' : 'HOST IP'
}
```

## Dependency Handling:

MIX will handle dependencies in a tree-like bottom-up fashion, retrieving the output of all of any IMs dependencies before making a request to that IM. IMs are not required to do dependency handling, as MIX will handle it. All IMs which have dependencies are assumed to not require location data.*

*(this is not consistent with MIX behavior, as MIX gives location data to IMs with dependencies.)

## Requirements for IMs:

- All IMs must have a '/' endpoint that can handle `GET` requests.
- All IMs must be on localhost to create a valid connection.
- All IMs must use `requests` to make HTTP requests.
- All IMs must return some JSON schema:
    - IMs which have dependencies are expected to be able to handle the JSON output of any of their dependencies.
    - IMs which do not have any dependency structure are expected to be able to handle the JSON sent by MIX to '/' described in the above section.

## Information Representation in MIX:

MIX will send the following JSON schema to all IMs which do not have any dependencies:

```
{
    'latitude' : float,
    'longitude' : float
}
```

For IMs with multiple dependencies, MIX will combine the latitude and longitude with the JSON schema of each dependency to send to that IM. Consider the following example:

IM 1 has dependencies 2 and 3.

IM 2 has the following schema:

```
{
    'distance' : float
}
```

IM 3 has the following schema:

```
{
    'squared_distance' : float
}
```

IM 1 will receive the following schema as input:

```
{
    'latitude' : float,
    'longitude' : float,
    'distance' : float,
    'squared_distance' : float
}
```

## Caching:

MIX will cache all responses from IMs. IMs must define the expiry age of their data in their responses, formatted as follows:

```
Cache-Control: max-age=x
```

where x is some arbitrary number.

Currently, MIX infers the `max-age` of all responses from the first IM response with non-zero `max-age`.
