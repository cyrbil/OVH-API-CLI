#!/usr/bin/env python
# -*- coding=utf-8 -*-
from __future__ import unicode_literals, absolute_import

import sys
import json
import hashlib
import logging

# noinspection PyProtectedMember, PyPackageRequirements
from pip._vendor import requests, os

logger = logging.getLogger(__name__)

__version__ = '1.0.4'


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if '-v' in args:
        args.pop(args.index('-v'))
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.getLogger('pip._vendor.requests').setLevel(logging.CRITICAL)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
        logging.getLogger('pip._vendor.requests').setLevel(logging.CRITICAL)

    if '-h' in args or '--help' in args:
        if '-h' in args:
            args.pop(args.index('-h'))
        if '--help' in args:
            args.pop(args.index('--help'))
        OvhApiCli.help()
        return 1

    try:
        logger.info('args: % r' % args)
        cli = OvhApiCli()
        if len(args) > 0 and args[0].startswith('--complete'):
            cli.parse_args(args[1:])
            cur = ''
            if '=' in args[0]:
                cur = args[0].split('=', 1)[1]
            logger.info('cur: %s' % cur)
            options = cli.autocomplete(cur)
            print(' '.join(options))
        else:
            cli.parse_args(args)
            try:
                data = cli.run()
            except AttributeError:
                return OvhApiCli.help()
            print(json.dumps(data, indent=2))
        return 0
    except Exception as err:
        logger.exception(err)
        logger.fatal('Fatal error occurred: %s' % err)
        return 1


# noinspection PyMethodMayBeStatic
class OvhApiCli(object):
    @staticmethod
    def help():
        print('Usage: ovhcli METHOD PATH [--args=value,]\n'
              'Tab completion can list available path, method and arguments')
        return 0

    def __init__(self, method=None, path=None, **kwargs):
        self.method = method
        self.path = path
        self.args = kwargs

    def __str__(self):
        return 'OVH_API_CLI(method=%r, path=%r, **%r)' % (self.method, self.path, self.args)

    def _sanitize_arg(self, arg):
        if (arg.startswith('"') and arg.endswith('"')) or \
           (arg.startswith("'") and arg.endswith("'")):
            arg = arg[1:-1]

        if '\{' in arg or '\}' in arg or '\ ' in arg:
            arg = arg.replace('\{', '{') \
                    .replace('\}', '}') \
                    .replace('\ ', ' ')
        return arg

    def parse_args(self, args):
        for arg in args:
            arg = self._sanitize_arg(arg)
            if arg.lower() in ['get', 'put', 'post', 'delete']:
                self.method = arg.lower()

            elif arg.startswith('/'):
                self.path = arg

            elif arg.startswith('--') and '=' in arg:
                k, v = arg.split('=', 1)
                self.args[k[2:]] = v
            else:
                logger.warn('Ignoring wrong argument %r' % arg)

        logger.debug(self)

    def autocomplete(self, cur):
        cur = self._sanitize_arg(cur)
        options = self.__autocomplete(cur)
        return [o for o in options if o.startswith(cur)]

    def run(self, schema=None):
        if not self.path:
            raise AttributeError('No path to query')
        if not self.method:
            raise AttributeError('No method to query')
        if not schema:
            root = requests.get('https://api.ovh.com/1.0/').json()
            root_paths = [api.get('path') for api in root.get('apis')]
            root_path = next((path for path in root_paths if self.path.startswith(path)), None)
            schema = requests.get('https://api.ovh.com/1.0%s.json' % root_path).json()

        # retrieve param list
        api = next(api for api in schema.get('apis')
                   if api.get('path') == self.path)

        op = next(op for op in api.get('operations')
                  if op.get('httpMethod').lower() == self.method)

        arguments = [param for param in op.get('parameters')]

        path_params = {}
        query_params = {}
        body_params = {}
        for arg in arguments:
            arg_type = arg.get('paramType')
            if arg_type == 'path':
                if arg.get('name') not in self.args:
                    raise Exception('Missing required path parameter %r' % arg.get('name'))
                path_params[arg.get('name')] = self.args.get(arg.get('name'))
            else:
                if arg_type == 'query':
                    params = query_params
                else:
                    params = body_params
                if arg.get('required', 0) and (arg.get('name') in self.args or arg.get('default')):
                    params[arg.get('name')] = self.args.get(arg.get('name')) or arg.get('default')
                else:
                    params[arg.get('name')] = self.args.get(arg.get('name')) or arg.get('default') or ''

        query_path = self.path.format(**path_params)
        return self.signed_call(self.method, query_path, query_params, body_params or None)

    def signed_call(self, method, path, query_params=None, body_params=None):
        if query_params is None:
            query_params = {}

        credentials = self.get_credentials()
        time = requests.get('https://eu.api.ovh.com/1.0/auth/time').content.decode('utf8')

        req = requests.Request(
            method, 'https://eu.api.ovh.com/1.0%s' % path, headers={
                'X-Ovh-Application': credentials.get('AK'),
                'X-Ovh-Timestamp': time,
                'X-Ovh-Consumer': credentials.get('CK')
            }, params=query_params, json=body_params
        )
        prepped = req.prepare()

        signature_str = '+'.join([
            credentials.get('AS'),
            credentials.get('CK'),
            prepped.method,
            prepped.url,
            prepped.body or '',
            time]).encode('utf8')

        prepped.headers['X-Ovh-Signature'] = '$1$' + hashlib.sha1(signature_str).hexdigest()

        res = requests.Session().send(prepped)

        return res.json()

    def __autocomplete(self, cur):
        root = requests.get('https://api.ovh.com/1.0/').json()
        root_paths = [api.get('path') for api in root.get('apis')]

        root_path = next((path for path in root_paths if (self.path or cur).startswith(path)), None)

        if not self.path:
            # if we are selecting a path, and root_path already present
            if cur and root_path and cur.startswith(root_path):
                pass
            else:
                return root_paths

        # we did not match...
        if not root_path:
            return []

        schema = requests.get('https://api.ovh.com/1.0%s.json' % root_path).json()

        # we are on a path
        if cur.startswith('/'):
            if self.path:  # if trying to add path twice
                return []
            else:
                return self.__autocomplete_path(schema, cur)

        # we are on an arguments
        elif cur.startswith('--'):
            if not self.path or not self.method:
                return []
            if '=' in cur:
                return self.__autocomplete_arguments_value(schema, cur)
            return self.__autocomplete_arguments(schema)

        # we are on nothing
        elif cur == '':
            if self.path and self.method:
                return self.__autocomplete_arguments(schema)
            elif self.path.endswith('/'):
                return self.__autocomplete_path(schema, cur)

        # already got method, not need to complete again
        if self.method:
            return []
        return self.__autocomplete_method(schema, cur)

    def __autocomplete_path(self, schema, cur):
        available_paths = [api.get('path') for api in schema.get('apis') if api.get('path').startswith(cur)]

        # reduce with only lowest paths
        # only keep /test if present and remove /test*
        sorted_path = sorted(available_paths)
        available_paths = []
        # brute force ... may be refactored
        for path in sorted_path:
            dodge = False
            for available_path in available_paths:
                if path.startswith(available_path) and available_path != cur:
                    dodge = True
            if dodge:
                continue
            available_paths.append(path)

        return available_paths

    def __autocomplete_method(self, schema, cur):
        api = next(api for api in schema.get('apis')
                   if api.get('path') == self.path)
        if not api:
            return []
        methods = [op.get('httpMethod') for op in api.get('operations')]
        if cur.islower():
            methods = [m.lower() for m in methods]
        return methods

    def __autocomplete_arguments(self, schema):
        api = next(api for api in schema.get('apis')
                   if api.get('path') == self.path)

        op = next(op for op in api.get('operations')
                  if op.get('httpMethod').lower() == self.method)

        arguments = [param.get('name') for param in op.get('parameters')
                     if param.get('name') not in self.args]

        return ['--%s=' % arg for arg in arguments]

    def __autocomplete_arguments_value(self, schema, cur):
        api = next(api for api in schema.get('apis')
                   if api.get('path') == self.path)

        op = next(op for op in api.get('operations')
                  if op.get('httpMethod').lower() == self.method)

        param = next(param for param in op.get('parameters')
                     if cur[2:-1] == param.get('name'))

        if param.get('paramType') == 'path':
            try:
                return self.__autocomplete_arguments_value_path(param)
            except Exception as err:
                logger.warn(err)
                return [param.get('name')]

        # todo: add completion for other type...
        return []

    def __autocomplete_arguments_value_path(self, param):
        arg_path = self.path[0:self.path.index(param.get('name')) - 1]
        # noinspection PyBroadException
        try:
            arg_path.format(self.args)  # raise if not all previous params
        except:
            raise Exception('Not all previous params are present')
        data = self.signed_call('GET', arg_path)
        if not isinstance(data, list):
            raise Exception('Unable to list for path param %r, api did not returned a list' % param.get('name'))
        return ['--%s=%s' % (param.get('name'), o) for o in data]

    def get_credentials(self):
        credentials_path = os.path.expanduser('~/.ovhcli')

        with open(credentials_path, 'r+') as f:
            data = json.load(f)

        for i in ['AK', 'AS', 'CK']:
            if i not in data:
                raise Exception('Need %r in %s' % (i, credentials_path))

        return data

"""
if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger('pip._vendor.requests').setLevel(logging.CRITICAL)

    test_args = [
        [],
        ['/'],
        ['/hosting/reseller'],
        ['/hosting/reseller/\{serviceName\}'],
        ['/hosting/reseller/{serviceName}/serviceInfos'],
        ['/hosting/reseller/{serviceName}/serviceInfos', 'GET'],
    ]

    test_set = [
        '', 'a', 'g', '/', '/h', '/hosting', '/hosting/resel', '/hosting/reseller/\{serviceName\}',
        '/hosting/reseller', '/hosting/reseller/', '/hosting/reseller/{serviceName}',
        '/hosting/reseller/{serviceName}/', '--serviceName='
    ]

    for a in test_args:
        print('\nTESTARGS(%r)' % a)
        c = OvhApiCli()
        c.parse_args(a)
        for t in test_set:
            print('TEST(%r): %s' % (t, ' '.join(c.autocomplete(t))))
        print('done')

    c = OvhApiCli()
    c.parse_args(['/hosting/reseller/{serviceName}/serviceInfos', 'GET', '--serviceName=hr-os5651-2'])
    data = c.run()
    print(json.dumps(data, indent=2))

#"""
