import os
import time
import sys
import kintone
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
#from datetime import datetime
from iotutils import getCurrentTimeStamp


def record_audio(file_path):
    result = os.system(f"ffmpeg -f pulse -i default  -t 30 -ar 16000 -ac 1 {file_path}")
    if result != 0:
        print(f"Error recording audio: ffmpeg returned {result}")
    else:
        print(f"Audio recorded successfully to {file_path}")


def analyze_audio(file_path, analyzer, sdomain, appId, token, worksheet):
    timeStamp = getCurrentTimeStamp()
    try:
        recording = Recording(
            analyzer,
            file_path,
            min_conf=0.82,
            )
        print(f"Analyzing audio file: {file_path}")
        recording.analyze()
        print(recording.detections)
        
        if not recording.detections:
            print("No detections found.")
            return
    
        #if recording.detections:
        fileKey = kintone.uploadFile(subDomain = sdomain,
                                     apiToken = token,
                                     filePath = file_path)
        if fileKey is None:
            print("Failed to upload file to Kintone.")
            return
        
        header_row = worksheet.row_values(1)
            
        for detection in recording.detections:
            common_name = detection.get('common_name', 'Unknown')
            scientific_name = detection.get('scientific_name', 'Unknown')
            confidence = int(detection.get('confidence', 0) * 100)
            confidence = f"{confidence}%"
            start_time = detection.get('start_time', 'Unknown')
            end_time = detection.get('end_time', 'Unknown')
            
            row_data = {"Time Stamp": timeStamp,
                        "Common Name": common_name,
                        "Scientific Name": scientific_name,
                        "Confidence": confidence,
                        "Start Time": start_time,
                        "End Time": end_time}
            
            ordered_data = [row_data.get(header, '') for header in header_row]
            
            worksheet.append_row(ordered_data)
            
            #worksheet.append_row([timestamp, common_name, scientific_name, confidence, start_time, end_time])
                
            payload = {"app": appId,
                       "record":{
                           "common_name":{"value":common_name},
                           "scientific_name":{"value":scientific_name},
                           "confidence":{"value":confidence},
                           "start_time":{"value":start_time},
                           "end_time":{"value":end_time},
                           "file_key":{"value":fileKey}}}
    
            recordId = kintone.uploadRecord(subDomain = sdomain,
                                            apiToken = token,
                                            record = payload)
            if recordId is None:
                print("Failed to upload record to Kintone.")
                return
            
    except Exception as e:
        print(f"Error during analysis: {e}")


                    
if __name__ == "__main__":
    sdomain = "sarasa"
    appId = "13"
    token = "py8RFDf3vMgA4TV9pQn60jvkG1837RGI0wscE9bL"
    
    worksheet = None
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("/home/pi/BirdNET-Pi/hackathon/credentials.json", scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key("1b8_iBOCQKR64TRKwOnBDUS5qPI4YYnSDyr7426mXF90")
        worksheet = spreadsheet.sheet1 
        print("Connected to Google Sheets successfully.")
    except gspread.exceptions.SpreadsheetNotFound:
        print("Spreadsheet not found. Please check the spreadsheet name and permissions.")
        sys.exit()
    except Exception as e:
        print(f"Failed to connect to Google Sheets: {e}")
        sys.exit()
    
    try:
        analyzer = Analyzer()
        print("BirdNET Analyzer initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize BirdNET Analyzer: {e}")
        sys.exit()
    
    while True:
        if worksheet is None:
            print("Worksheet is not defined.")
            break
        
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_path = f"/home/pi/BirdNET-Pi/hackathon/_{timestamp}.wav"
            record_audio(file_path)
            analyze_audio(file_path, analyzer, sdomain, appId, token, worksheet)
            
            time.sleep(0)
        
        except KeyboardInterrupt:
            print("Process interrupted by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")