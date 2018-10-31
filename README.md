# noraina-ansible
Ansible modules for Noraina services

## Requirements
- Ansible 2.5.2+

## Install
https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html#adding-a-module-locally

## Usage
### Manage instances
```yml
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
```
### Manage certificates
```yml
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
```