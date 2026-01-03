from http import client
from time import timezone
from config import in_production, function_name
import base64
import json
import warnings
from pretty_html_table import build_table
from dates import init_time
from datetime import datetime
from helper import execution_logger
import pandas as pd

warnings.filterwarnings("ignore")


def send_alerts(event, context):
    try:
        time = datetime.now()
        if in_production:
            print("In production")
            pubsub_msg = base64.b64decode(event['data']).decode('utf-8')
            json_data = json.loads(pubsub_msg)
            period = json_data['period']
            account = json_data['account']
            project_id = json_data['project_id'].lower()
            asset = json_data.get('asset', 'all')
            cl_timezone = json_data['timezone']
            init_time(cl_timezone)
            dataset_id = json_data['dataset_id']
            # location = json_data['location']
            location = 'watchdog-test'
            # fail_safe_emails = 'mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com'
            print(f"period - {period} account - {account} project_id - {project_id} location - {location}")
            #update_story_sent_info(project_id, dataset_id, timezone)

        else:
            print("Not in production")
            period = 'daily'
            # period = 'weekly'
            account = 'Levis'
            project_id = 'watchdog-340107'
            asset = 'Levis PH 24'
            cl_timezone = 'Asia/Manila'
            init_time(cl_timezone)
            dataset_id = 'levis_ph_24_watchdog'
            location = 'watchdog-test'
            fail_safe_emails = 'srikar.kolli@sarasanalytics.com, mohith.das@sarasanalytics.com, sai.harshith@sarasanalytics.com'
        
        #Reason for Importing Module here - Cause the Dates need to be Initialized before we start the functions
        from start_alerts import start_alerts
        start_alerts(project_id, dataset_id, account, period, asset, cl_timezone)
        data = {
        "date": time,
        "function":function_name,
        "input_operands": f"Project:{project_id}, Dataset:{dataset_id}",
        "status": True,
        "description": "Sent alert"
        }
        execution_logger(client, project_id, pd.DataFrame(data))
        print("Function executed successfully")

    except Exception as e:
        data = {
        "date": time,
        "function":function_name,
        "input_operands": f"Project:{project_id}, Dataset:{dataset_id}",
        "status": False,
        "description": e
        }
        execution_logger(client, project_id, pd.DataFrame(data))
    


if not in_production:

    send_alerts(None, None)
