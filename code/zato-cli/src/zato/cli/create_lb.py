# -*- coding: utf-8 -*-

"""
Copyright (C) 2010 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Zato
from zato.cli import common_logging_conf_contents, ZatoCommand, ZATO_LB_DIR
from zato.common.defaults import http_plain_server_port

# bzrlib
from bzrlib.lazy_import import lazy_import

lazy_import(globals(), """
    # quicli
    import os, uuid
    
""")

config_template = """{
  "haproxy_command": "haproxy",
  "host": "localhost",
  "port": 20151,
  "keyfile": "./lba-priv-key.pem",
  "certfile": "./lba-cert.pem",
  "ca_certs": "./ca-chain.pem",
  "work_dir": "../",
  "verify_fields": {},
  "log_config": "./logging.conf",
  "pid_file": "zato-lb-agent.pid"
}
"""

zato_config_template = """
# ##############################################################################

global
    log 127.0.0.1:514 local0 debug # ZATO global:log
    stats socket {stats_socket} # ZATO global:stats_socket

# ##############################################################################

defaults
    log global
    option httpclose

    stats uri /zato-lb-stats # ZATO defaults:stats uri

    timeout connect 15000 # ZATO defaults:timeout connect
    timeout client 15000 # ZATO defaults:timeout client
    timeout server 15000 # ZATO defaults:timeout server

    stats enable
    stats realm   Haproxy\ Statistics

    # Note: The password below is a UUID4 written in plain-text.
    stats auth    admin1:{stats_password}

    stats refresh 5s

# ##############################################################################

backend bck_http_plain
    mode http
    balance roundrobin
    
# ZATO begin backend bck_http_plain

{default_backend}

# ZATO end backend bck_http_plain

# ##############################################################################

frontend front_http_plain

    mode http
    default_backend bck_http_plain

    option httplog # ZATO frontend front_http_plain:option log-http-requests
    bind 127.0.0.1:11223 # ZATO frontend front_http_plain:bind
    maxconn 200 # ZATO frontend front_http_plain:maxconn

    monitor-uri /zato-lb-alive # ZATO frontend front_http_plain:monitor-uri
"""

default_backend="""
    server http_plain--zato-quickstart-server-01 127.0.0.1:{server01_port} check inter 2s rise 2 fall 2 # ZATO backend bck_http_plain:server--zato-quickstart-server-01
    server http_plain--zato-quickstart-server-02 127.0.0.1:{server02_port} check inter 2s rise 2 fall 2 # ZATO backend bck_http_plain:server--zato-quickstart-server-02
"""

class Create(ZatoCommand):
    command_name = 'create lb-agent'

    needs_empty_dir = True

    def __init__(self, args):
        super(Create, self).__init__(args)
        self.target_dir = os.path.abspath(args.path)

    def execute(self, args, use_default_backend=False, server02_port=None, show_output=True):

        os.mkdir(os.path.join(self.target_dir, 'config'))
        os.mkdir(os.path.join(self.target_dir, 'config', 'zdaemon'))
        os.mkdir(os.path.join(self.target_dir, 'logs'))

        log_path = os.path.join(self.target_dir, 'logs', 'lb-agent.log')
        stats_socket = os.path.join(self.target_dir, 'haproxy-stat.sock')

        open(os.path.join(self.target_dir, 'config', 'lb-agent.conf'), 'w').write(config_template)
        open(os.path.join(self.target_dir, 'config', 'logging.conf'), 'w').write((common_logging_conf_contents.format(log_path=log_path)))
        
        if use_default_backend:
            backend = default_backend.format(server01_port=http_plain_server_port, server02_port=server02_port)
        else:
            backend = '\n# ZATO default_backend_empty'

        zato_config = zato_config_template.format(stats_socket=stats_socket,
                stats_password=uuid.uuid4().hex, default_backend=backend)
        open(os.path.join(self.target_dir, 'config', 'zato.config'), 'w').write(zato_config)
        
        # Initial info
        self.store_initial_info(self.target_dir, self.COMPONENTS.LOAD_BALANCER.code)

        if show_output:
            if self.verbose:
                msg = "Successfully created a load-balancer's agent in {}".format(self.target_dir)
                self.logger.debug(msg)
            else:
                self.logger.info('OK')
