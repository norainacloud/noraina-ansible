#!/usr/bin/python

DOCUMENTATION = '''
---
module: noraina_ece_instance
short_description: Manage Noraina ECE instances
description: This module allows you to interact with Noraina's ECE API to manage instances.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
    api_url: "https://nacp01.noraina.net"
    mail: "user@example.com"
    password: "password"
  tasks:
    - name: Create an instance
      ece_instance:
        api_url: "{{api_url}}"
        mail: "{{mail}}"
        password: "{{password}}"
        state: "present"
        name: "my_instance"
        services:
          - { name: "my_service_1",
              fqdn: "my-service-1.domain.com",
              origin_hostheader: "my-service-1.s3-eu-west-1.amazonaws.com",
              origin_backend: "http://my-service-1.s3-eu-west-1.amazonaws.com",
              provider_region: "eu-west-1",
              provider_name: "aws" }
          - { name: "my_service_2",
              fqdn: "another-service.domain.com",
              origin_hostheader: "my-service-bucket.s3-eu-west-1.amazonaws.com",
              origin_backend: "http://my-service-bucket.s3-eu-west-1.amazonaws.com",
              provider_region: "eu-west-2",
              provider_name: "aws" }
      register: create
    - debug: var=create

    - name: Update an instance
      ece_instance:
        api_url: "{{api_url}}"
        mail: "{{mail}}"
        password: "{{password}}"
        state: "present"
        name: "my_instance"
        services:
          - { name: "my_change_1",
              fqdn: "my-change-1.domain.com",
              origin_hostheader: "my-change-1.s3-eu-west-1.amazonaws.com",
              origin_backend: "http://my-change-1.s3-eu-west-1.amazonaws.com",
              provider_region: "eu-west-1",
              provider_name: "aws" }
          - { name: "my_service_2",
              fqdn: "another-service.domain.com",
              origin_hostheader: "my-service-bucket.s3-eu-west-1.amazonaws.com",
              origin_backend: "http://my-service-bucket.s3-eu-west-1.amazonaws.com",
              provider_region: "eu-west-2",
              provider_name: "aws" }
      register: update
    - debug: var=update

    - name: Delete an instance
      ece_instance:
        api_url: "{{api_url}}"
        mail: "{{mail}}"
        password: "{{password}}"
        state: "present"
        name: "my_instance"
      register: delete
    - debug: var=delete
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def ece_instance(data):
    # login to ece_api
    headers = {
        "Content-Type": "application/json"
    }
    url = "{}{}" . format(data['api_url'], '/login')
    response = requests.post(url, json.dumps(data), headers=headers)
    login = response.json()

    if response.status_code == 401:
        return False, "Authentication failed.", False, login

    if response.status_code == 200:
        headers = {
            "Content-Type": "application/json",
            "x-access-token": login['data']['token']
        }

        # get all instances list
        url = "{}{}" . format(data['api_url'], '/instance')
        response = requests.get(url, headers=headers)
        instances = response.json()

        if response.status_code == 500:
            err_msg = "Something went wrong getting instance data."
            return True, err_msg, False, response.json()

        if response.status_code == 200:
            if data['state'] == "present":
                instance = next(
                (inst for inst in instances if inst['name'] == data['name']), None)
                # if we find a matching instance name it's an update
                if instance is not None:
                    if data.has_key('services'):
                        for index, service in enumerate(instance['services']):
                            check = instance
                            del check['services'][index]['created_date']
                            del check['services'][index]['_id']
                        # if services have changed it's an update
                        if ordered(check['services']) != ordered(data['services']):
                            url = "{}{}/{}" . format(data['api_url'],
                                                    '/instance', instance['_id'])
                            del data['api_url']
                            del data['name']
                            del data['state']
                            response = requests.put(
                                url, json.dumps(data), headers=headers)
                            return False, None, True, response.json()
                        # if services are equal, let's just print out the instance
                        else:
                            return False, None, False, instance
                    else:
                        err_msg = "No services information provided."
                        meta = {"status": response.status_code,
                                'response': response.json()}
                        return True, err_msg, False, meta
                # if no instance matches, it must be a create.
                else:
                    if data.has_key('services'):
                        url = "{}{}" . format(data['api_url'], '/instance')
                        del data['api_url']
                        del data['state']
                        response = requests.post(
                            url, json.dumps(data), headers=headers)
                        return False, None, True, response.json()
                    else:
                        err_msg = "No services information provided."
                        meta = {"status": response.status_code,
                                'response': response.json()}
                        return True, err_msg, False, meta
            elif data['state'] == "absent":
                instance = next(
                    (inst for inst in instances if inst['name'] == data['name']), None)
                if instance is not None:
                    url = "{}{}/{}" . format(data['api_url'],
                                                '/instance', instance['_id'])
                    response = requests.delete(url, headers=headers)
                    return False, None, True, response.json()
                else:
                    err_msg = "No instance found by this name."
                    meta = {"status": response.status_code,
                            'response': response.json()}
                    return True, err_msg, False, meta

    # default: something went wrong
    meta = {"status": response.status_code, 'response': response.json()}
    return True, "Something went wrong", False, meta


def main():
    fields = {
        "api_url": {"required": True, "type": "str"},
        "mail": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "state": {"required": True, "type": "str"},
        "name": {"required": False, "type": "str"},
        "services": {"required": False, "type": "list"}
    }

    module = AnsibleModule(argument_spec=fields)
    is_error, error_msg, has_changed, result = ece_instance(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg=error_msg, meta=result)


if __name__ == '__main__':
    main()
