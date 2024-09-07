import sys
import time
import kintone
import weatherhat
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from iotutils import getCurrentTimeStamp


sensor = weatherhat.WeatherHAT()


sdomain = "sarasa"
appId = "13"
token = "py8RFDf3vMgA4TV9pQn60jvkG1837RGI0wscE9bL"


worksheet = None


try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("/home/pi/weatherhat-python/examples/credentials.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1b8_iBOCQKR64TRKwOnBDUS5qPI4YYnSDyr7426mXF90")
    worksheet = spreadsheet.sheet1  # 1?????????
    print("Connected to Google Sheets successfully.")
except gspread.exceptions.SpreadsheetNotFound:
    print("Spreadsheet not found. Please check the spreadsheet name and permissions.")
except Exception as e:
    print(f"Failed to connect to Google Sheets: {e}")
    sys.exit()


print("""
basic.py - Basic example showing how to read Weather HAT's sensors.
Press Ctrl+C to exit!
""")




while True:
    try:
        sensor.update(interval=60.0)


        wind_direction_cardinal = sensor.degrees_to_cardinal(sensor.wind_direction)


        print(f"""
    System temp: {sensor.device_temperature:0.2f} *C
    Temperature: {sensor.temperature:0.2f} *C


    Humidity:    {sensor.humidity:0.2f} %
    


    Light:       {sensor.lux:0.2f} Lux


    Pressure:    {sensor.pressure:0.2f} hPa


    Wind (avg):  {sensor.wind_speed:0.2f} m/sec


    Rain:        {sensor.rain:0.2f} mm/sec


    Wind (avg):  {sensor.wind_direction:0.2f} degrees ({wind_direction_cardinal})


    """)


        header_row = worksheet.row_values(1)
        
        timeStamp = getCurrentTimeStamp()
        system_temp = f"{sensor.device_temperature:0.2f}*C"
        temperature = f"{sensor.temperature:0.2f}*C"
        humidity = f"{sensor.humidity:0.2f}%"
       #dew_point = f"{sensor.dewpoint:0.2f}*C"
        light = f"{sensor.lux:0.2f} Lux"
        pressure = f"{sensor.pressure:0.2f} hPa" 
        wind_avg_speed = f"{sensor.wind_speed:0.2f} m/sec"
        rain = f"{sensor.rain:0.2f} mm/sec"
        wind_avg_direction = f"{sensor.wind_direction:0.2f}, degree ({wind_direction_cardinal})"
        
        #file_paths = f"{system_temp}, {temperature}, {humidity}, {dew_point}, {light}, {pressure}, {wind_avg_speed}, {rain}, {wind_avg_direction}"
        
        row_data = {"Time Stamp": timeStamp,
                    "System Temp": system_temp,
                    "Temperature": temperature,
                    "Humidity": humidity,
                    #"Dew Point": dew_point,
                    "Light": light,
                    "Pressure": pressure,
                    "Wind & Speed": wind_avg_speed,
                    "Rain": rain,
                    "Wind & Direction": wind_avg_direction}
        
        ordered_data = [row_data.get(header, '') for header in header_row]
        worksheet.append_row(ordered_data)
        
        file_content = f"""System temp: {system_temp} *C
                           Temperature: {temperature} *C
                           Humidity:    {humidity} %
                           Light:       {light} Lux
                           Pressure:    {pressure} hPa
                           Wind (avg):  {wind_avg_speed} m/sec
                           Rain:        {rain} mm/sec
                           Wind (avg):  {wind_avg_direction}
                           """


        file_path = "/home/pi/weather_data.txt"
        with open(file_path, "w") as file:
            file.write(file_content)
        
        fileKey = kintone.uploadFile(
        subDomain=sdomain,
        apiToken=token,
        filePath = file_path)


        payload = {
        "app": appId,
        "record": {
        "system_temp": {"value": system_temp},
        "temperature": {"value": temperature},
        "humidity": {"value": humidity},
        #"dew_point": {"value": dew_point},
        "light": {"value": light},
        "pressure": {"value": pressure},
        "wind_avg_speed": {"value": wind_avg_speed},
        "rain": {"value": rain},
        "wind_avg_direction": {"value": wind_avg_direction},
        "wind_direction_cardinal": {
            "value": [{"fileKey": fileKey}]
        }
    }
}
                   
        recordId = kintone.uploadRecord(subDomain = sdomain,
                                     apiToken = token,
                                     record = payload)
        if recordId is None:
            sys.exit()
            
        time.sleep(600.0)
    except KeyboardInterrupt:
        break