# -*- coding: utf-8 -*-

import os
import urllib.parse as urlparse  # pip install urllib3
from os.path import expanduser

from configobj import ConfigObj  # pip install configobj


class ResourceLoader():

    @classmethod
    def load_from_locations(self, filename, locations):
        """
        :rtype filename: str
        :rtype locations: [str]
        :return: {}
        """

        for location in locations:
            url = urlparse.urlparse(location)

            if url.scheme == 'home':
                base_path = expanduser('~').replace('\\', '/') + url.path
                file_path = os.path.join(base_path, filename)

                if os.path.isfile(file_path):
                    properties = ConfigObj(file_path)
                    return properties
            elif url.scheme in ('file', 'path'):
                file_path = os.path.join(url.path, filename)
                if os.path.isfile(file_path):
                    properties = ConfigObj(file_path)
                    return properties
            elif url.scheme == 'http' or \
                    url.scheme == 'https':
                if not location.endswith('/'):
                    location += '/'
                file_path = location + filename
                try:
                    file = urllib.urlopen(file_path)
                    print(file)
                except:
                    pass

        return {}
