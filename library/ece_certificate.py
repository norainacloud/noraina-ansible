#!/usr/bin/python

DOCUMENTATION = '''
---
module: noraina_ece_certificate
short_description: Manage Noraina ECE certificates
description: This module allows you to interact with Noraina's ECE API to manage certificates.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
    api_url: "https://nacp01.noraina.net"
    mail: "user@example.com"
    password: "password"
  tasks:
    - name: Upload a certificate with certificate chain
      ece_certificate:
        api_url: "{{api_url}}"
        mail: "{{mail}}"
        password: "{{password}}"
        state: "present"
        name: "my_certificate_01"
        key: "{{ lookup('file', '/some/path/key.pem') }}"
        cert: "{{ lookup('file', '/some/path/cert.pem') }}"
        chain: "{{ lookup('file', '/some/path/chain.pem') }}"
      register: upload
    - debug: var=upload

    - name: Delete a certificate
      ece_certificate:
        api_url: "{{api_url}}"
        mail: "{{mail}}"
        password: "{{password}}"
        state: "absent"
        name: "my_old_certificate"
      register: delete
    - debug: var=delete
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import json
import base64


def ece_certificate(data):
    # login to ece_api
    headers = {
        "Content-Type": "application/json"
    }
    url = "{}{}" . format(data['api_url'], '/login')
    response = requests.post(url, json.dumps(data), headers=headers)
    del data['mail']
    del data['password']
    login = response.json()

    if response.status_code == 401:
        return False, "Authentication failed.", False, login
    if response.status_code == 200:
        headers = {
            "Content-Type": "application/json",
            "x-access-token": login['data']['token']
        }

        # get user's certificate list
        url = "{}{}" . format(data['api_url'], '/certificate')
        response = requests.get(url, headers=headers)
        certificates = response.json()

        if response.status_code == 500:
            err_msg = "Something went wrong getting certificate data."
            return True, err_msg, False, response.json()

        if response.status_code == 200:
            if data['state'] == "present":
                certificate = next(
                (cert for cert in certificates['data'] if cert['name'] == data['name']), None)
                # if we find a name already, just print out the certificate info.
                if certificate is not None:
                    result={}
                    result['data']=certificate
                    result['status']="success"
                    return False, None, False, result
                # if certificate and key are not found, let's upload a new one
                else:
                    if data.has_key('key') and data.has_key('cert'):
                        if data['chain'] is not None:
                            data['chain'] = data['chain'].rstrip()
                        data['key'] = data['key'].rstrip()
                        data['cert'] = data['cert'].rstrip()

                        files = {
                            "key": data['key'],
                            "cert": data['cert'],
                            "chain": data['chain']
                        }
                        url = "{}{}" . format(data['api_url'], '/certificate')
                        del data['api_url']
                        del data['state']
                        del data['key']
                        del data['cert']
                        del data['chain']
                        del headers['Content-Type']
                        response = requests.post(
                            url, data, files=files, headers=headers)
                        return False, None, True, response.json()
                    else:
                        err_msg = "No certificate and/or key provided."
                        meta = {"status": response.status_code,
                                'response': response.json()}
                        return True, err_msg, False, meta
            # if state is absent, delete the certificate
            elif data['state'] == "absent":
                certificate = next(
                    (cert for cert in certificates['data'] if cert['name'] == data['name']), None)
                if certificate is not None:
                    url = "{}{}/{}" . format(data['api_url'],
                                                '/certificate', certificate['_id'])
                    response = requests.delete(url, headers=headers)
                    return False, None, True, response.json()
                else:
                    err_msg = "No certificate found by this name."
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
        "name": {"required": True, "type": "str"},
        "key": {"required": False, "type": "str"},
        "cert": {"required": False, "type": "str"},
        "chain": {"required": False, "type": "str"}
    }

    module = AnsibleModule(argument_spec=fields)
    is_error, error_msg, has_changed, result = ece_certificate(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg=error_msg, meta=result)


if __name__ == '__main__':
    main()
