# -*- coding: utf-8 -*-
import os
from subprocess import Popen, PIPE, call

from modules import cbpi, app
from modules.core.hardware import SensorPassive
import json
import os, re, threading, time
from flask import Blueprint, render_template, request
from modules.core.props import Property

from pyowfs import Connection

blueprint = Blueprint('one_wire_owfs', __name__)

temp = 22

root = Connection('localhost:4304')

arr        = []

def getSensors():
    try:
        arr = []

        for s in root.find (family="28"): 
            dirname = s.get("address")
            if dirname in arr:
                ##cbpi.app.logger.info("Device %s Found (Thermometer on owfs); double entry: skipped." % dirname)
                pass
            else:
                cbpi.app.logger.info("Device %s Found (Family: %s, ID: %s, Type: %s, Thermometer on owfs)" % ( s.get("address"), s.get("family"), s.get("id"), s.get("type") ))
                arr.append(s.get("address"))
        for s in root.find (family="10"): 
            dirname = s.get("address")
            if dirname in arr:
                ##cbpi.app.logger.info("Device %s Found (Thermometer on owfs); double entry: skipped." % dirname)
                pass
            else:
                cbpi.app.logger.info("Device %s Found (Family: %s, ID: %s, Type: %s, Thermometer on owfs)" % ( s.get("address"), s.get("family"), s.get("id"), s.get("type") ))
                arr.append(s.get("address"))
        return arr
    except:
        return []


class myThread (threading.Thread):

    value = 0


    def __init__(self, sensor_name):
        threading.Thread.__init__(self)
        self.value = 0
        self.sensor_name = sensor_name
        self.runnig = True

    def shutdown(self):
        pass

    def stop(self):
        self.runnig = False

    def run(self):

        while self.runnig:
            try:
                ##app.logger.info("READ OWFS TEMP %s" % (self.sensor_name))
                ## Test Mode
                if self.sensor_name is None:
                    self.value = 0     ##sensor.temperature
                    app.logger.info("READ OWFS TEMP %s; self.sensor_name is None" % (self.sensor_name))
                    break
                
                x=root.find(address=self.sensor_name)[0]
                x.use_cache (0)
                self.value = float(x.get("temperature"))

                app.logger.info("READ OWFS TEMP %s; temp: %04f" % (self.sensor_name, self.value))
            except:
                pass

            time.sleep(4)



@cbpi.sensor
class ONE_WIRE_OWFS_SENSOR(SensorPassive):

    sensor_name = Property.Select("Sensor", getSensors(), description="The OneWire OWFS sensor address.")
    offset = Property.Number("Offset", True, 0, description="Offset which is added to the received sensor data. Positive and negative values are both allowed.")

    def init(self):

        self.t = myThread(self.sensor_name)

        def shudown():
            shudown.cb.shutdown()
        shudown.cb = self.t

        self.t.start()

    def stop(self):
        try:
            self.t.stop()
        except:
            pass

    def read(self):
        if self.get_config_parameter("unit", "C") == "C":
            self.data_received(round(self.t.value + self.offset_value(), 2))
        else:
            self.data_received(round(9.0 / 5.0 * self.t.value + 32 + self.offset_value(), 2))

    @cbpi.try_catch(0)
    def offset_value(self):
        return float(self.offset)
            
    @classmethod
    def init_global(self):
        try:
            ##call(["modprobe", "w1-gpio"])
            ##call(["modprobe", "w1-therm"])
            pass
        except Exception as e:
            pass


@blueprint.route('/<int:t>', methods=['GET'])
def set_temp(t):
    global temp
    temp = t
    return ('', 204)


@cbpi.initalizer()
def init(cbpi):

    cbpi.app.register_blueprint(blueprint, url_prefix='/api/one_wire_owfs')
