#!/usr/bin/env python3
#--*-- coding:utf-8 --*--

#
# Update GoDaddy DNS "A" Record.
#
# usage: godaddy_ddns.py [-h] [--version] [--ip IP] [--key KEY]
#                        [--secret SECRET] [--ttl TTL]
#                        hostname
#
# positional arguments:
#   hostname         DNS fully-qualified host name with an 'A' record
#
# optional arguments:
#   -h, --help       show this help message and exit
#   --version        show program's version number and exit
#   --ip IP          DNS Address (defaults to public WAN address from http://ipv4.icanhazip.com/)
#   --key KEY        GoDaddy production key
#   --secret SECRET  GoDaddy production secret
#   --ttl TTL        DNS TTL.
#
# GoDaddy customers can obtain values for the KEY and SECRET arguments by creating a production key at 
# https://developer.godaddy.com/keys/.  
# 
# Note that command line arguments may be specified in a FILE, one to a line, by instead giving
# the argument "%FILE".  For security reasons, it is particularly recommended to supply the 
# KEY and SECRET arguments in such a file, rather than directly on the command line:
#
# Create a file named, e.g., `godaddy-ddns.config` with the content:
#   MY.FULLY.QUALIFIED.HOSTNAME.COM
#   --key
#   MY-KEY-FROM-GODADDY
#   --secret
#   MY-SECRET-FROM-GODADDY
#
# Then just invoke `godaddy-ddns %godaddy-ddns.config`

import argparse
import requests
import sys
import os
import json

if sys.version_info > (3,):
  from urllib.request import urlopen, Request
  from urllib.error import URLError, HTTPError
else:
  from urllib2 import urlopen, Request
  from urllib2 import URLError, HTTPError

prog = 'moonmoonbird-godaddy-ddns'
version = '0.1'
author = 'lomoonmoonbird@gmail.com'

parser = argparse.ArgumentParser(description="update moonmoonbird's home A record", 
fromfile_prefix_chars='%', epilog= \
'''GoDaddy customers can obtain values for the KEY and SECRET arguments by creating a production key at 
https://developer.godaddy.com/keys/.  
Note that command line arguments may be specified in a FILE, one to a line, by instead giving
the argument "%FILE".  For security reasons, it is particularly recommended to supply the 
KEY and SECRET arguments in such a file, rather than directly on the command line.''')


parser.add_argument('--version', action='version', version="{} {}".format(prog, version))
parser.add_argument('hostname', type=str, default=None, help='domain name for A record')
parser.add_argument('--ip', type=str, default=None, help='IP address to be updated (default to public wan address from http://api.ipify.org)')
parser.add_argument('--key', type=str, default=None, help='godaddy key')
parser.add_argument('--secret', type=str, default=None, help='godaddy secret')
parser.add_argument('--ttl', type=int, default=3600, help='godaddy dns ttl')

args = parser.parse_args()


godaddy_update_dns_api = 'https://api.godaddy.com/v1/domains/{domain}/records/{type}/{name}'

godaddy_update_dns_api_2 = 'https://api.godaddy.com/v1/domains/{domain}/records'

def main():
    print (args)
    #hostname
    hostname = args.hostname
    hostname_split = hostname.split('.')

    #validate hostname
    if len(hostname_split) < 3:
        msg = 'hostname "{}" must be in the form HOST.DOMAIN.TOP'.format(hostname)
        raise Exception(msg)

       
    #get public ip from wan
    if not args.ip:
        # while True:
        try:
            with urlopen("http://api.ipify.org") as f: resp=f.read()
            if sys.version_info > (3,): resp = resp.decode('utf-8')
            args.ip = resp.strip()
            print (args.ip)
        except URLError:
            msg = 'Unable to automatically obtain IP address from http://api.ipify.org.'
            raise Exception(msg)
            # with open('./ip.txt', 'wr') as ipf:
            #     for ip in ipf:
            #         if args.ip == ip:
                        
            
    ip = args.ip
    ip_split =ip.split('.')

    #validate ip
    try:
        ip_1 = int(ip_split[0])
        ip_2 = int(ip_split[1])
        ip_3 = int(ip_split[2])
        ip_4 = int(ip_split[3])

        if len(ip_split) != 4 or int(ip_split[0]) > 255 or int(ip_split[1]) > 255 or int(ip_split[2]) > 255 or int(ip_split[3]) > 255:
            raise ValueError
    except ValueError as ve:
        msg = 'ip "{}" is not valid'.format(ip)
        raise Exception(msg)

    url = godaddy_update_dns_api.format(domain='.'.join(hostname_split[1:]), type='A', name=hostname_split[0])
    # url = godaddy_update_dns_api_2.format(domain='.'.join(hostname_split[1:]))
    # headers = {
    #     'Authorization': 'sso-key '+args.key + ":" + args.secret,
    #     'Content-Type': 'application/json',
    # }

    data = json.dumps([{"type":"A","name": hostname,"data": args.ip,"ttl":3600}])
    # data = json.dumps([{"data": '10.10.10.10', "ttl": args.ttl, "name": hostname_split[0], "type": "A"}])

    if sys.version_info > (3, ):
        data = data.encode('utf-8')
    
    # response = requests.put(url, headers=headers ,data = data)

    # import requests
    # headers = {
    #     'Authorization': 'sso-key '+args.key + ":" + args.secret,
    #     'Content-Type': 'application/json',
    # }
    # data = json.dumps([{"type":"A","name": hostname ,"data": args.ip,"ttl":3600}])
    # response = requests.put('https://api.godaddy.com/v1/domains/moonmoonbird.com/records/A/cloud', headers=headers, data=data)
    # print(response.content)

    req = Request(url, method='PUT', data=data)

    req.add_header("Content-Type","application/json")
    req.add_header("Accept","application/json")
    if args.key and args.secret:
        req.add_header("Authorization", "sso-key {}:{}".format(args.key,args.secret))
        print ("Authorization", "sso-key {}:{}".format(args.key,args.secret), '@@@@@@')

    try:
        with urlopen(req) as f: resp = f.read()
        if sys.version_info > (3,):  resp = resp.decode('utf-8')
        resp = json.loads(resp)
    except HTTPError as e:
        if e.code==400:
            msg = 'Unable to set IP address: GoDaddy API URL ({}) was malformed.'.format(req.full_url)
        elif e.code==401:
            if args.key and args.secret:
                msg = '''Unable to set IP address: --key or --secret option incorrect.
                Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a % file.'''
            else:
                msg = '''Unable to set IP address: --key or --secret option missing.
        Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a % file.'''
        elif e.code==403:
            msg = '''Unable to set IP address: customer identified by --key and --secret options denied permission.
    Correct values can be obtained from from https://developer.godaddy.com/keys/ and are ideally placed in a % file.'''
        elif e.code==404:
            msg = 'Unable to set IP address: {} not found at GoDaddy.'.format(args.hostname)
        elif e.code==422:
            msg = 'Unable to set IP address: "{}" has invalid domain or lacks A record.'.format(args.hostname)
        elif e.code==429:
            msg = 'Unable to set IP address: too many requests to GoDaddy within brief period.'
        else:
            msg = 'Unable to set IP address: GoDaddy API failure because "{}".'.format(e.reason)
        raise Exception(msg)
    except URLError(e):
        msg = 'Unable to set IP address: GoDaddy API failure because "{}".'.format(e.reason)
        raise Exception(msg)
    
    print('IP address for {} set to {}.'.format(args.hostname,args.ip)) 

if __name__ == '__main__':
    main()
# curl -X PUT https://api.godaddy.com/v1/domains/moonmoonbird.com/records -H 'Authorization: sso-key dL3d1Kb6AcX7_FrxJfrRtkxPRk3QwWHTxmi:GseVHdUA7pnnj9of8KruVr' -H 'Content-Type: application/json' --data '[{"type":"A","name":"cloud","data":"192.168.1.1","ttl":3600}]'
# curl -X PUT https://api.godaddy.com/v1/domains/moonmoonbird.com/records/A/cloud -H 'Authorization: sso-key dL3d1Kb6AcX7_FrxJfrRtkxPRk3QwWHTxmi:GseVHdUA7pnnj9of8KruVr' -H 'Content-Type: application/json' --data '[{"type":"A","name":"cloud.moonmoonbird.com","data":"192.168.1.4","ttl":3600}]'