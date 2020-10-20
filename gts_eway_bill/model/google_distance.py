# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

import urllib
import urllib.parse

try:
    import json
except ImportError:
    import simplejson as json
from openerp.osv import orm
from openerp.tools.translate import _

api_key_list = ['AIzaSyDn62nmAZhfTnluOi1iPbd-KtgrE4jGXeE','AIzaSyBdf9p4X0CcBzYT4p9uAnYKrwKlqyxz4SQ',
                        'AIzaSyDYexaKXuEIX2XEnDNnK1oUkOMOolXb','AIzaSyD0FtOTNu4eQ6pyzjxPcWRKZulcVtudvMc',
                        'AIzaSyBAsD8KrFwzD0bAxPi2js6NEcSEoysUoTw','AIzaSyDYOZcxvqCIL9svD7W5B-An7Varn2yj4AI']
def fetch_json(query_url, params={}, headers={}):
    """Retrieve a JSON object from a (parameterized) URL.
    
    :param query_url: The base URL to query
    :type query_url: string
    :param params: Dictionary mapping (string) query parameters to values
    :type params: dict
    :param headers: Dictionary giving (string) HTTP headers and values
    :type headers: dict 
    :return: A `(url, json_obj)` tuple, where `url` is the final,
    parameterized, encoded URL fetched, and `json_obj` is the data 
    fetched from that URL as a JSON-format object. 
    :rtype: (string, dict or array)
    ::::::USEFULL LINKS:::::::::::::::::::::
    http://maps.googleapis.com/maps/api/distancematrix/json?origins=Vancouver+BC|Seattle&destinations=San+Francisco|Victoria+BC&mode=bicycling&language=fr-FR&key=API_KEY
    https://developers.google.com/maps/documentation/distancematrix/
    http://maps.googleapis.com/maps/api/directions/json?origin=Chicago,IL&destination=Los+Angeles,CA&waypoints=Joplin,MO|Oklahoma+City,OK&key=API_KEY

    """
    encoded_params = urllib.parse.urlencode(params)
    url = query_url + encoded_params
    #print "url.........",url
    request = urllib.request(url, headers=headers)
    response = urllib.request.urlopen(request)
    return (url, json.load(response))


class google_maps_distance(object):
    _DIRECTIONS_QUERY_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?'

    def __init__(self, referrer_url=''):
        self.referrer_url = referrer_url

    def directions(self, origins, destinations, mode='driving', **kwargs):
        """ Get directions from 'origin' to 'destination'. """
        api_key = False
        if kwargs:
            for key,value in kwargs.items():
                api_key = value if key == 'key' else False
        params = {
            'origins': origins,
            'destinations': destinations,
            'mode': mode,
            'key' : api_key
        }
#        print "params++++++++++++++++++++++++++++++++",params
        params.update({'departure_time':kwargs.get('departure_time',False)})
        #complete_response = []
        #print "start......."
        url, response = fetch_json(self._DIRECTIONS_QUERY_URL, params=params)
#        print "url ,response.......",url,response
        #complete_response.append
        status_code = response['status']
        if status_code != 'OK':
            raise orm.except_orm(_('ERROR !'), _('Impossible to access data'))
        return response
#    {'response':response, 'api_count':api_count, 'last_count':last_count}
    
    def duration(self, origin, destination, mode='driving', **kwargs):
        response = self.directions(origin, destination, mode, **kwargs)
        duration = 0
        rows = response.get('rows')
        if rows:
            elements = rows[0].get('elements')
            if elements:
                duration = elements[0].get('duration', {}).get('text', 0)
        return duration
    
    def distance(self, origins, destinations, mode='driving', **kwargs):
        response = self.directions(origins, destinations, mode, **kwargs)
        
        result = {}
        result['duration'] = []
        result['distance'] = []
        rows = response.get('rows') 
        if rows:
            for each_row in rows:
            #print "rows......",rows
                elements = each_row.get('elements')
                #print "elements.........",elements
                if elements:
                    #print "elements.........",elements[0]
                    result['distance'].append(elements[0].get('distance', {}).get('value', 0))
                    result['duration'].append(elements[0].get('duration', {}).get('text', 0))
                else:
                    result['distance'].append(0)
                    result['duration'].append(0)
#                result['api_count']= response.get('api_count',False)
#                result['last_count']= response.get('last_count',False)
        return result
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: