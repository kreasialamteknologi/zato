# -*- coding: utf-8 -*-

"""
Copyright (C) 2012 Dariusz Suchojad <dsuch at gefira.pl>

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

# stdlib
from copy import deepcopy
from threading import RLock

# mx
from mx.Tools import NotGiven

# Bunch
from bunch import SimpleBunch

class ConfigDict(object):
    """ Stores configuration of a particular item of interest, such as an
    outgoing HTTP connection. Could've been a dict and we wouldn't have been using
    .get and .set but things like connection names aren't necessarily proper
    Python attribute names. Also, despite certain dict operations being atomic
    in CPython, the class employs a threading.Lock in critical places so the code
    doesn't assume anything about CPython's byte code-specific implementation
    details.
    """
    def __init__(self, name, _bunch=None):
        self.name = name
        self._bunch = _bunch
        self.lock = RLock()
        
    def get(self, key):
        with self.lock:
            return self._bunch[key]
        
    def set(self, key, value):
        with self.lock:
            self._bunch[key] = value
            
    def __del__(self, key):
        with self.lock:
            del self._bunch[key]
            
    def copy(self):
        """ Returns a new instance of ConfigDict with items copied over from self.
        """
        config_dict = ConfigDict(self.name)
        config_dict._bunch = SimpleBunch()
        config_dict._bunch.update(self._bunch)
        
        return config_dict
            
    @staticmethod        
    def from_query(name, query_data, item_class=SimpleBunch):
        """ Return a new ConfigDict with items taken from an SQL query.
        """
        config_dict = ConfigDict(name)
        config_dict._bunch = SimpleBunch()

        if query_data:
            query, attrs = query_data
    
            for item in query:
                config_dict._bunch[item.name] = SimpleBunch()
                config_dict._bunch[item.name].config = SimpleBunch()
                
                for attr_name in attrs.keys():
                    config_dict._bunch[item.name]['config'][attr_name] = getattr(item, attr_name)
            
        return config_dict

class ConfigStore(object):
    """ The central place for storing a Zato server configuration. May /not/ be
    shared across threads - each thread should get its own copy using the .copy
    method.
    """
    def __init__(self, ftp=NotGiven, plain_http=NotGiven, soap=NotGiven, s3=NotGiven, 
                 sql_conn=NotGiven, amqp=NotGiven, jms_wmq=NotGiven, zmq=NotGiven,
                 repo_location=NotGiven, basic_auth=NotGiven, wss=NotGiven, tech_acc=NotGiven,
                 url_sec=NotGiven, http_soap=NotGiven, broker_config=NotGiven):
        
        # Outgoing connections
        self.ftp = ftp                              # done
        self.plain_http = plain_http                # not yet
        self.soap = soap                            # not yet
        self.s3 = s3                                # not yet
        self.sql_conn = sql_conn                    # not yet
        self.amqp = amqp                            # not yet
        self.jms_wmq = jms_wmq                      # not yet
        self.zmq = zmq                              # not yet
        
        # Local on-disk configuraion repository
        self.repo_location = repo_location          # done
        
        # Security definitions
        self.basic_auth = basic_auth                # done
        self.wss = wss                              # done
        self.tech_acc = tech_acc                    # done
        
        # URL security
        self.url_sec = url_sec                      # done
        
        # HTTP/SOAP channels
        self.http_soap = http_soap                  # done
        
        # Configuration for broker clients
        self.broker_config = broker_config          # done
        
    def copy(self):
        config_store = ConfigStore()
        
        # Grab all ConfigDicts - even if they're actually NotGiven - and make their copies
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, ConfigDict):
                copy_meth = getattr(attr, 'copy')
                setattr(config_store, attr_name, copy_meth())
            elif attr is NotGiven:
                setattr(config_store, attr_name, NotGiven)

        config_store.url_sec = self.url_sec
        config_store.broker_config = self.broker_config
                
        return config_store
    
#
# ftp = self.outgoing.ftp.get('aaa')
# ------------------------------------
# self.outgoing -> ConfigStore
# self.outgoing.ftp -> ConfigDict
# self.outgoing.ftp.get('aaa') -> SimpleBunch
# self.outgoing.ftp.get('aaa').config -> connection parameters
# self.outgoing.ftp.get('aaa').conn -> connection object
#

# amqp = self.outgoing.amqp.get('aaa')
# jms_wmq = self.outgoing.jms_wmq.get('aaa')
# zmq = self.outgoing.zmq.get('aaa')

# ftp = self.outgoing.ftp.get('aaa')
# plain_http = self.outgoing.plain_http.get('aaa')
# s3 = self.outgoing.s3.get('aaa')
# soap = self.outgoing.soap.get('aaa')
# sql_conn = self.sql_pool.get('aaa')
# del self.outgoing.ftp['aaa']

# config_copy = copy.copy(outgoing)
# ftp_copy = copy.copy(outgoing.ftp)
