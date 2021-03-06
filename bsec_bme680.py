import subprocess, json, configparser
from statistics import median

config = configparser.ConfigParser()
config.read('config/config.txt')

MQTT_HOST = config.get('SETTINGS', 'MQTT_HOST')
MQTT_TOPIC = config.get('SETTINGS', 'MQTT_TOPIC')
MQTT_USER = config.get('SETTINGS', 'MQTT_USER')
MQTT_PASSWORD = config.get('SETTINGS', 'MQTT_PASSWORD')
MQTT_PORT = config.get('SETTINGS', 'MQTT_PORT')
MQTT_CAFILE = config.get('SETTINGS', 'MQTT_CAFILE')
MQTT_CRT = config.get('SETTINGS', 'MQTT_CRT')
MQTT_KEY = config.get('SETTINGS', 'MQTT_KEY')

# Open C File
proc = subprocess.Popen(['./bsec_bme680', 'secondary'], stdout=subprocess.PIPE)

listIAQ_Accuracy = []
listPressure = []
listGas = []
listTemperature = []
listIAQ = []
listHumidity = []
listStatus = []


def pub_mqtt(jsonrow):
    cmd = ['mosquitto_pub', '-d', '--cafile', MQTT_CAFILE, '--cert', MQTT_CRT, '--key', MQTT_KEY, '-h', MQTT_HOST, '-t',
           MQTT_TOPIC, '-p', MQTT_PORT, '-u', MQTT_USER, '-P', MQTT_PASSWORD, '-r', '-s']
    print(jsonrow)
    with subprocess.Popen(cmd, shell=False, bufsize=0, stdin=subprocess.PIPE, encoding='utf-8').stdin as f:
        json.dump(jsonrow, f)


for line in iter(proc.stdout.readline, ''):
    lineJSON = json.loads(line.decode("utf-8"))  # process line-by-line
    lineDict = dict(lineJSON)

    listIAQ_Accuracy.append(int(lineDict['iaq_accuracy']))
    listPressure.append(float(lineDict['pressure']))
    listGas.append(int(lineDict['eco2_ppm']))
    listTemperature.append(float(lineDict['temperature']))
    listIAQ.append(float(lineDict['iaq']))
    listHumidity.append(float(lineDict['humidity']))
    listStatus.append(int(lineDict['bsec_status']))

    if len(listIAQ_Accuracy) == 20:
        # generate the median for each value
        IAQ_Accuracy = median(listIAQ_Accuracy)
        Pressure = median(listPressure)
        Gas = median(listGas)
        Temperature = median(listTemperature)
        IAQ = median(listIAQ)
        Humidity = median(listHumidity)
        Status = median(listStatus)

        # clear lists
        listIAQ_Accuracy.clear()
        listPressure.clear()
        listGas.clear()
        listTemperature.clear()
        listIAQ.clear()
        listHumidity.clear()
        listStatus.clear()

        # Temperature Offset
        Temperature = Temperature + 2

        # Convert the Fahrenheit
        Temperature = (Temperature * 9 / 5) + 32

        payload = {"IAQ_Accuracy": IAQ_Accuracy,
                   "IAQ": round(IAQ, 1),
                   "Temperature": round(Temperature, 1),
                   "Humidity": round(Humidity, 1),
                   "Pressure": round(Pressure, 1),
                   "Gas": Gas,
                   "Status": Status}

        pub_mqtt(payload)
