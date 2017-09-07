# -*- coding: utf-8 -*-
#
# 2017 Darko Poljak (darko.poljak at gmail.com)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import configparser
import os
import multiprocessing
import cdist.configuration as cc
import os.path as op
import argparse
from cdist import test
import cdist.argparse as cap


my_dir = op.abspath(op.dirname(__file__))
fixtures = op.join(my_dir, 'fixtures')


class ConfigurationOptionsTestCase(test.CdistTestCase):

    def test_OptionBase(self):
        option = cc.OptionBase('test')
        test_cases = (
            ([], [], True, None, ),
            (['spam', 'eggs', ], [], True, ['spam', 'eggs', ], ),
            ([], ['spam', 'eggs', ], True, ['spam', 'eggs', ], ),
            (
                ['spam', 'eggs', ],
                ['ham', 'spamspam', ],
                True,
                ['spam', 'eggs', 'ham', 'spamspam', ],
            ),
            (['spam', 'eggs', ], 'spam:eggs', True, 'spam:eggs', ),
            ('spam:eggs', ['spam', 'eggs', ], True, ['spam', 'eggs', ], ),
            ('spam', 'eggs', True, 'eggs', ),

            (['spam', 'eggs', ], 'spam:eggs', True, 'spam:eggs', ),

            ('spam:eggs', ['spam', 'eggs', ], False,  ['spam', 'eggs', ], ),
            ('spam', 'eggs', False, 'eggs', ),
            (
                ['spam', 'eggs', ],
                ['ham', 'spamspam', ],
                False,
                ['ham', 'spamspam', ],
            ),
        )
        for currval, newval, update_appends, expected in test_cases:
            self.assertEqual(
                option.update_value(currval, newval,
                                    update_appends=update_appends),
                expected)

    def test_StringOption(self):
        option = cc.StringOption('test')
        self.assertIsNone(option.translate(''))
        self.assertEqual(option.translate('spam'), 'spam')
        converter = option.converter()
        self.assertEqual(converter('spam'), 'spam')
        self.assertIsNone(converter(''))

    def test_BooleanOption(self):
        option = cc.BooleanOption('test')
        for x in cc.BooleanOption.BOOLEAN_STATES:
            self.assertEqual(option.translate(x),
                             cc.BooleanOption.BOOLEAN_STATES[x])
        converter = option.converter()
        self.assertRaises(ValueError, converter, 'of')
        for x in cc.BooleanOption.BOOLEAN_STATES:
            self.assertEqual(converter(x), cc.BooleanOption.BOOLEAN_STATES[x])

    def test_IntOption(self):
        option = cc.IntOption('test')
        converter = option.converter()
        self.assertRaises(ValueError, converter, 'x')
        for x in range(-5, 10):
            self.assertEqual(converter(str(x)), x)

    def test_LowerBoundIntOption(self):
        option = cc.LowerBoundIntOption('test', -1)
        converter = option.converter()
        self.assertRaises(ValueError, converter, -2)
        for x in range(-1, 10):
            self.assertEqual(converter(str(x)), x)

    def test_SpecialCasesLowerBoundIntOption(self):
        special_cases = {
            -1: 8,
            -2: 10,
        }
        option = cc.SpecialCasesLowerBoundIntOption('test', -1, special_cases)
        for x in special_cases:
            self.assertEqual(option.translate(x), special_cases[x])

    def test_SelectOption(self):
        valid_values = ('spam', 'eggs', 'ham', )
        option = cc.SelectOption('test', valid_values)
        converter = option.converter()
        self.assertRaises(ValueError, converter, 'spamspam')
        for x in valid_values:
            self.assertEqual(converter(x), x)

    def test_DelimitedValuesOption(self):
        option = cc.DelimitedValuesOption('test', ':')
        converter = option.converter()
        value = 'spam:eggs::ham'
        self.assertEqual(converter(value), ['spam', 'eggs', 'ham', ])
        self.assertIsNone(converter(''))


class ConfigurationTestCase(test.CdistTestCase):

    def setUp(self):
        # Create test config file.
        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }
        config_custom = configparser.ConfigParser()
        config_custom['GLOBAL'] = {
            'parallel': '4',
            'archiving': 'txz',
        }

        config_custom2 = configparser.ConfigParser()
        config_custom2['GLOBAL'] = {
            'parallel': '16',
            'archiving': 'tbz2',
            'remote_copy': 'myscp',
        }

        self.expected_config_dict = {
            'GLOBAL': {
                'beta': False,
                'local_shell': '/bin/sh',
                'remote_shell': '/bin/sh',
                'inventory_dir': None,
                'cache_path_pattern': None,
                'conf_dir': None,
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': None,
                'remote_exec': None,
                'jobs': 0,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': None,
            },
        }

        self.config_file = os.path.join(fixtures, 'cdist.cfg')
        with open(self.config_file, 'w') as f:
            config.write(f)

        self.custom_config_file = os.path.join(fixtures, 'cdist_custom.cfg')
        with open(self.custom_config_file, 'w') as f:
            config_custom.write(f)

        self.custom_config_file2 = os.path.join(fixtures, 'cdist_custom2.cfg')
        with open(self.custom_config_file2, 'w') as f:
            config_custom2.write(f)

        config['TEST'] = {}
        self.invalid_config_file1 = os.path.join(fixtures,
                                                 'cdist_invalid1.cfg')
        with open(self.invalid_config_file1, 'w') as f:
            config.write(f)

        del config['TEST']
        config['GLOBAL']['test'] = 'test'
        self.invalid_config_file2 = os.path.join(fixtures,
                                                 'cdist_invalid2.cfg')
        with open(self.invalid_config_file2, 'w') as f:
            config.write(f)

        del config['GLOBAL']['test']
        config['GLOBAL']['archiving'] = 'zip'
        self.invalid_config_file3 = os.path.join(fixtures,
                                                 'cdist_invalid3.cfg')
        with open(self.invalid_config_file3, 'w') as f:
            config.write(f)

        self.maxDiff = None

    def tearDown(self):
        os.remove(self.config_file)
        os.remove(self.custom_config_file)
        os.remove(self.custom_config_file2)
        os.remove(self.invalid_config_file1)
        os.remove(self.invalid_config_file2)
        os.remove(self.invalid_config_file3)

        # remove files from tests
        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        custom_config_file = os.path.join(fixtures, 'cdist-custom.cfg')
        if os.path.exists(global_config_file):
            os.remove(global_config_file)
        if os.path.exists(local_config_file):
            os.remove(local_config_file)
        if os.path.exists(custom_config_file):
            os.remove(custom_config_file)

    def test_singleton(self):
        x = cc.Configuration(None)
        args = argparse.Namespace()
        args.a = 'a'
        y = cc.Configuration(args)
        self.assertIs(x, y)

    def test_non_singleton(self):
        x = cc.Configuration(None, singleton=False)
        args = argparse.Namespace()
        args.a = 'a'
        y = cc.Configuration(args, singleton=False)
        self.assertIsNot(x, y)

    def test_read_config_file(self):
        config = cc.Configuration(None, env={}, config_files=())
        d = config._read_config_file(self.config_file)
        self.assertEqual(d, self.expected_config_dict)

        for x in range(1, 4):
            config_file = getattr(self, 'invalid_config_file' + str(x))
            with self.assertRaises(ValueError):
                config._read_config_file(config_file)

    def test_read_env_var_config(self):
        config = cc.Configuration(None, env={}, config_files=())
        env = {
            'a': 'a',
            'CDIST_BETA': '1',
            'CDIST_PATH': '/usr/local/cdist:~/.cdist',
        }
        expected = {
            'beta': True,
            'conf_dir': ['/usr/local/cdist', '~/.cdist', ],
        }
        section = 'GLOBAL'
        d = config._read_env_var_config(env, section)
        self.assertEqual(d, expected)

        del env['CDIST_BETA']
        del expected['beta']
        d = config._read_env_var_config(env, section)
        self.assertEqual(d, expected)

    def test_read_args_config(self):
        config = cc.Configuration(None, env={}, config_files=())
        args = argparse.Namespace()
        args.beta = False
        args.conf_dir = ['/usr/local/cdist1', ]
        args.verbose = 3
        args.tag = 'test'

        expected = {
            'conf_dir': ['/usr/local/cdist1', ],
            'verbosity': 3,
        }
        args_dict = vars(args)
        d = config._read_args_config(args_dict)
        self.assertEqual(d, expected)
        self.assertNotEqual(d, args_dict)

    def test_update_config_dict(self):
        config = {
            'GLOBAL': {
                'conf_dir': ['/usr/local/cdist', ],
                'parallel': -1,
            },
        }
        newconfig = {
            'GLOBAL': {
                'conf_dir': ['~/.cdist', ],
                'parallel': 2,
                'local_shell': '/usr/local/bin/sh',
            },
        }
        expected = {
            'GLOBAL': {
                'conf_dir': ['/usr/local/cdist', '~/.cdist', ],
                'parallel': 2,
                'local_shell': '/usr/local/bin/sh',
            },
        }
        configuration = cc.Configuration(None, env={}, config_files=())
        configuration._update_config_dict(config, newconfig,
                                          update_appends=True)
        self.assertEqual(config, expected)
        expected = {
            'GLOBAL': {
                'conf_dir': ['~/.cdist', ],
                'parallel': 2,
                'local_shell': '/usr/local/bin/sh',
            },
        }
        configuration._update_config_dict(config, newconfig,
                                          update_appends=False)
        self.assertEqual(config, expected)

    def test_update_config_dict_section(self):
        config = {
            'GLOBAL': {
                'conf_dir': ['/usr/local/cdist', ],
                'parallel': -1,
            },
        }
        newconfig = {
            'conf_dir': ['~/.cdist', ],
            'parallel': 2,
            'local_shell': '/usr/local/bin/sh',
        }
        expected = {
            'GLOBAL': {
                'conf_dir': ['/usr/local/cdist', '~/.cdist', ],
                'parallel': 2,
                'local_shell': '/usr/local/bin/sh',
            },
        }
        configuration = cc.Configuration(None, env={}, config_files=())
        configuration._update_config_dict_section('GLOBAL', config, newconfig,
                                                  update_appends=True)
        self.assertEqual(config, expected)
        expected = {
            'GLOBAL': {
                'conf_dir': ['~/.cdist', ],
                'parallel': 2,
                'local_shell': '/usr/local/bin/sh',
            },
        }
        configuration._update_config_dict_section('GLOBAL', config, newconfig,
                                                  update_appends=False)
        self.assertEqual(config, expected)

    def test_configuration1(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
        }
        args = argparse.Namespace()
        expected_config_dict = {
            'GLOBAL': {
                'verbosity': 0,
            },
        }

        # bypass singleton so we can test further
        cc.Configuration.instance = None
        configuration = cc.Configuration(args, env=env,
                                         config_files=('cdist.cfg'))
        self.assertIsNotNone(configuration.args)
        self.assertIsNotNone(configuration.env)
        self.assertIsNotNone(configuration.config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration2(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': False,
                'local_shell': '/bin/sh',
                'remote_shell': '/bin/sh',
                'inventory_dir': None,
                'cache_path_pattern': None,
                'conf_dir': None,
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': None,
                'remote_exec': None,
                'jobs': 0,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': None,
            },
        }
        config_files = (global_config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration3(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/var/db/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': ['/opt/cdist', ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'myscp',
                'remote_exec': 'myexec',
                'jobs': 0,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'tar',
            },
        }
        config_files = (global_config_file, local_config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration4(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': None,
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/cdist/conf',
                    '/usr/local/share/cdist/conf',
                ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': None,
                'remote_exec': None,
                'jobs': 0,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': None,
            },
        }
        config_files = (global_config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration5(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/var/db/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/cdist/conf',
                    '/usr/local/share/cdist/conf',
                ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'myscp',
                'remote_exec': 'myexec',
                'jobs': 0,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'tar',
            },
        }
        config_files = (global_config_file, local_config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_update_defaults_for_unset(self):
        config = {
            'GLOBAL': {
            },
        }
        expected_config = {
            'GLOBAL': {
                'verbosity': 0,
            },
        }
        cfg = cc.Configuration(None, env={}, config_files=())
        cfg._update_defaults_for_unset(config)
        self.assertEqual(config, expected_config)

    def test_configuration6(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        args.inventory_dir = '/opt/sysadmin/cdist/inventory'
        args.conf_dir = ['/opt/sysadmin/cdist/conf', ]
        args.manifest = '/opt/sysadmin/cdist/conf/manifest/init'
        args.jobs = 10
        args.verbose = None

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/opt/sysadmin/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/cdist/conf',
                    '/usr/local/share/cdist/conf',
                    '/opt/sysadmin/cdist/conf',
                ],
                'init_manifest': '/opt/sysadmin/cdist/conf/manifest/init',
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'myscp',
                'remote_exec': 'myexec',
                'jobs': 10,
                'parallel': multiprocessing.cpu_count(),
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'tar',
            },
        }
        config_files = (global_config_file, local_config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration7(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'conf_dir': '/opt/conf/cdist',
            'remote_copy': 'scpcustom',
            'remote_exec': 'sshcustom',
            'parallel': '15',
            'archiving': 'txz',
        }

        custom_config_file = os.path.join(fixtures, 'cdist-custom.cfg')
        with open(custom_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/var/db/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/conf/cdist',
                ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'scpcustom',
                'remote_exec': 'sshcustom',
                'jobs': 0,
                'parallel': 15,
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'txz',
            },
        }

        config_files = (global_config_file, local_config_file, )

        args.config_file = custom_config_file

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration8(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'conf_dir': '/opt/conf/cdist',
            'remote_copy': 'scpcustom',
            'remote_exec': 'sshcustom',
            'parallel': '15',
            'archiving': 'txz',
        }

        custom_config_file = os.path.join(fixtures, 'cdist-custom.cfg')
        with open(custom_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/var/db/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/conf/cdist',
                ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'scpcustom',
                'remote_exec': 'sshcustom',
                'jobs': 0,
                'parallel': 15,
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'txz',
            },
        }

        config_files = (global_config_file, local_config_file, )

        os.environ['CDIST_CONFIG_FILE'] = custom_config_file

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

    def test_configuration_get_args(self):
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'TEST': 'test',
            'CDIST_PATH': '/opt/cdist/conf:/usr/local/share/cdist/conf',
            'REMOTE_COPY': 'scp',
            'REMOTE_EXEC': 'ssh',
            'CDIST_BETA': '1',
            'CDIST_LOCAL_SHELL': '/usr/bin/sh',
            'CDIST_REMOTE_SHELL': '/usr/bin/sh',
        }
        args = argparse.Namespace()

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'off',
            'local_shell': '/bin/sh',
            'remote_shell': '/bin/sh',
            'inventory_dir': '',
            'cache_path_pattern': '',
            'conf_dir': '',
            'init_manifest': '',
            'out_path': '',
            'remote_out_path': '',
            'remote_copy': '',
            'remote_exec': '',
            'jobs': '0',
            'parallel': '-1',
            'verbosity': 'INFO',
            'archiving': 'none',
        }

        global_config_file = os.path.join(fixtures, 'cdist-global.cfg')
        with open(global_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'beta': 'on',
            'local_shell': '/usr/bin/sh',
            'remote_shell': '/usr/bin/sh',
            'inventory_dir': '/var/db/cdist/inventory',
            'conf_dir': '/opt/cdist',
            'remote_copy': 'myscp',
            'remote_exec': 'myexec',
            'parallel': '-1',
            'archiving': 'tar',
        }

        local_config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(local_config_file, 'w') as f:
            config.write(f)

        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'conf_dir': '/opt/conf/cdist',
            'remote_copy': 'scpcustom',
            'remote_exec': 'sshcustom',
            'parallel': '15',
            'archiving': 'txz',
        }

        custom_config_file = os.path.join(fixtures, 'cdist-custom.cfg')
        with open(custom_config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'beta': True,
                'local_shell': '/usr/bin/sh',
                'remote_shell': '/usr/bin/sh',
                'inventory_dir': '/var/db/cdist/inventory',
                'cache_path_pattern': None,
                'conf_dir': [
                    '/opt/conf/cdist',
                ],
                'init_manifest': None,
                'out_path': None,
                'remote_out_path': None,
                'remote_copy': 'scpcustom',
                'remote_exec': 'sshcustom',
                'jobs': 0,
                'parallel': 15,
                'verbosity': cap.VERBOSE_INFO,
                'archiving': 'txz',
            },
        }

        config_files = (global_config_file, local_config_file, )

        os.environ['CDIST_CONFIG_FILE'] = custom_config_file

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        configuration = cc.Configuration(args, env=env,
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)

        args = configuration.get_args()
        dargs = vars(args)
        expected_args = {
            'beta': True,
            'inventory_dir': '/var/db/cdist/inventory',
            'cache_path_pattern': None,
            'conf_dir': [
                '/opt/conf/cdist',
            ],
            'manifest': None,
            'out_path': None,
            'remote_out_path': None,
            'remote_copy': 'scpcustom',
            'remote_exec': 'sshcustom',
            'jobs': 0,
            'parallel': 15,
            'verbose': cap.VERBOSE_INFO,
            'use_archiving': 'txz',
        }

        self.assertEqual(dargs, expected_args)

    def test_configuration_empty_value_in_file(self):
        config = configparser.ConfigParser()
        config['GLOBAL'] = {
            'inventory_dir': '',
            'conf_dir': '',
        }

        config_file = os.path.join(fixtures, 'cdist-local.cfg')
        with open(config_file, 'w') as f:
            config.write(f)

        expected_config_dict = {
            'GLOBAL': {
                'inventory_dir': None,
                'conf_dir': None,
                'verbosity': 0,
            },
        }

        config_files = (config_file, )

        # bypass singleton so we can test further
        cc.Configuration.instance = None

        args = argparse.Namespace()
        configuration = cc.Configuration(args, env={},
                                         config_files=config_files)
        self.assertEqual(configuration.config, expected_config_dict)


if __name__ == "__main__":
    import unittest

    unittest.main()