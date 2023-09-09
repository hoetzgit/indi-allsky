#!/usr/bin/env python3

#import sys
import io
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import socket
import ssl
import requests
import logging
import math
import time
import ephem
from pprint import pformat  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging


ELEVATION = 300

### ATL
LATITUDE   = 33.7
LONGITUDE  = -84.4

### San Francisco
#LATITUDE  = 37.6
#LONGITUDE = -122.4

### NYC
#LATITUDE  = 40.7
#LONGITUDE = -74.0

### Milwaukee
#LATITUDE  = 43.0
#LONGITUDE = -87.9

### Prince Albert
#LATITUDE  = 53.2
#LONGITUDE = -105.8

### WINNIPEG
#LATITUDE  = 49.9
#LONGITUDE = -97.1

### CALGARY
#LATITUDE  = 51.0
#LONGITUDE = -114.1



class IssTrack(object):
    iss_tle_url = 'https://live.ariss.org/iss.txt'
    iss_temp_file = '/tmp/iss_27272897.txt'


    def __init__(self):
        self.iss_tle_data = None


    def main(self):
        iss_temp_file_p = Path(self.iss_temp_file)


        now = datetime.now()
        now_minus_24h = now - timedelta(hours=24)


        # allow data to be reused
        if not self.iss_tle_data:
            try:
                if not iss_temp_file_p.exists():
                    self.iss_tle_data = self.download_tle(self.iss_tle_url, iss_temp_file_p)
                elif iss_temp_file_p.stat().st_mtime < now_minus_24h.timestamp():
                    logger.warning('KML is older than 24 hours')
                    self.iss_tle_data = self.download_tle(self.iss_tle_url, iss_temp_file_p)
                else:
                    self.iss_tle_data = self.load_tle(iss_temp_file_p)
            except socket.gaierror as e:
                logger.error('Name resolution error: %s', str(e))
                self.hms_kml_data = None
            except socket.timeout as e:
                logger.error('Timeout error: %s', str(e))
                self.iss_tle_data = None
            except ssl.SSLCertVerificationError as e:
                logger.error('Certificate error: %s', str(e))
                self.iss_tle_data = None
            except requests.exceptions.SSLError as e:
                logger.error('Certificate error: %s', str(e))
                self.iss_tle_data = None



        if self.iss_tle_data:
            obs = ephem.Observer()
            obs.lon = math.radians(LONGITUDE)
            obs.lat = math.radians(LATITUDE)
            obs.elevation = ELEVATION  # meters

            iss = ephem.readtle(*self.iss_tle_data)
            #logger.info('%s', dir(iss))


            while True:
                obs.date = datetime.utcnow()
                #obs.date = datetime.utcnow() + timedelta(hours=6)  # testing

                iss.compute(obs)
                iss_next_pass = obs.next_pass(iss)

                logger.info('iss: altitude %4.1f deg, azimuth %5.1f deg', math.degrees(iss.alt), math.degrees(iss.az))
                logger.info(' next rise: {0:%Y-%m-%d %H:%M:%S}, max: {1:%Y-%m-%d %H:%M:%S}, set: {2:%Y-%m-%d %H:%M:%S} - duration {3:d}s'.format(
                    ephem.localtime(iss_next_pass[0]),
                    ephem.localtime(iss_next_pass[2]),
                    ephem.localtime(iss_next_pass[4]),
                    (ephem.localtime(iss_next_pass[4]) - ephem.localtime(iss_next_pass[0])).seconds,
                ))

                time.sleep(5.0)



    def download_tle(self, url, tmpfile):
        logger.warning('Downloading %s', url)
        r = requests.get(url, allow_redirects=True, verify=True, timeout=15.0)

        if r.status_code >= 400:
            logger.error('URL returned %d', r.status_code)
            return None

        with io.open(tmpfile, 'w') as f_tle:
            f_tle.write(r.text)


        return r.text.splitlines()


    def load_tle(self, tmpfile):
        logger.warning('Loading tle data: %s', tmpfile)
        with io.open(tmpfile, 'r') as f_tle:
            tle_data = f_tle.readlines()


        return tle_data


if __name__ == "__main__":
    a = IssTrack()
    a.main()


