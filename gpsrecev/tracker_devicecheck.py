# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import checkNet

#from usr.modules.sensor import Sensor
from usr.modules.logging import getLogger
from usr.modules.location import Location
#from usr.modules.temp_humidity_sensor import TempHumiditySensor
from usr.settings import PROJECT_NAME, PROJECT_VERSION, settings

log = getLogger(__name__)


class DeviceCheck(object):

    def __init__(self):
        self.__locator = None
        #self.__sensor = None
        self.__temp_humidity = None

    def add_module(self, module):
        if isinstance(module, Location):
            self.__locator = module
            return True
        #elif isinstance(module, Sensor):
        #    self.__sensor = module
        #    return True
        #elif isinstance(module, TempHumiditySensor):
        #    self.__temp_humidity = module
        #    return True
        return False

    def net(self):
        current_settings = settings.get()
        checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)
        timeout = current_settings.get("sys", {}).get("checknet_timeout", 60)
        check_res = checknet.wait_network_connected(timeout)
        log.debug("DeviceCheck.net res: %s" % str(check_res))
        return check_res

    def location(self):
        # return True if OK
        if not self.__locator:
            raise TypeError("self.__locator is not registered")

        gps_data = None
        loc_info = self.__locator.read(retry=30)
        for k, v in loc_info.items():
            gps_data = v
            if gps_data:
                break

        return True if gps_data else False

    #def temp(self):
    #    # return True if OK
    #    res = False
    #    if self.__temp_humidity is None:
    #        res = None
    #    else:
    #        if self.__temp_humidity.on():
    #            temperature, humidity = self.__temp_humidity.read()
    #            if temperature is not None and humidity is not None:
    #                res = True
    #            self.__temp_humidity.off()
    #    return res

    def light(self):
        # return True if OK
        return None

    def triaxial(self):
        # return True if OK
        return None

    def mike(self):
        # return True if OK
        return None
