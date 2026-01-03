from http import client
from time import timezone
from config import in_production, dict_email_config
import warnings
from pretty_html_table import build_table
from helper import update_story_sent_info
from send_ppt import send_ppt_to_slack, send_mail
from dates import yesterday, current_date, get_previous_week_start_date_end_date
from create_ppt import create_ppt


def start_alerts(project_id, dataset_id, account, period, asset, cl_timezone):
    
    try:
        # print(yesterday, year_ago, six_months_ago, three_months_ago, sdlw, hourly_date_start, current_date)
        dict_ppts, dict_neg_warn_count, dict_neg_crit_count, dict_tot_count = create_ppt(project_id, account, period, asset)

        # print(f'Fail_df: \n{fail_df}')

        # if len(fail_df) > 0:
        #     print('Sending mail for non-updated datasets')
        #     message = "Hi Team,<br><br>" + \
        #               "<h1>Below are the datasets for levis that didn't update while generating ppt:</h1><br><br>"
        #     end_message = f"<br><br>Please check for any potential issues!<br><br>Regards,<br>Watchdog Team,<br>Saras Analytics."
        #     send_mail(recipient=fail_safe_emails,
        #               cc="",
        #               subject=f'Watchdog Project - Levis PPT Status Alert /report',
        #               message=message + build_table(fail_df, 'blue_light', font_size='13px') + end_message,
        #               filepath=None,
        #               type='html')

        for asset in dict_ppts.keys():
            total_count = dict_tot_count[asset]
            negative_warning_count = dict_neg_warn_count[asset]
            negative_critical_count = dict_neg_crit_count[asset]
            ppt = dict_ppts[asset]
            email_config = dict_email_config[asset]

            if total_count == 0:
                message_anomaly = "No Alerts"

            elif any([negative_critical_count, negative_warning_count]):
                message_anomaly = "‼️ "
                if negative_critical_count:
                    message_anomaly = message_anomaly + f" {negative_critical_count} {'Critical alert' if negative_critical_count == 1 else 'Critical alerts'}"
                if negative_warning_count:
                    message_anomaly = message_anomaly + f" {negative_warning_count} {'Warning alert' if negative_warning_count == 1 else 'Warning alerts'}"
            else:
                message_anomaly = f"{total_count} {'Positive alert' if total_count == 1 else 'Positive alerts'}"

            if period == 'daily':
                filename = f"Anomaly alerts for {asset} {yesterday.strftime('%d-%m-%Y')}.pptx"

            elif period == 'weekly':
                week_start, _ = get_previous_week_start_date_end_date(current_date)
                filename = f"Anomaly alerts for {asset} Week {week_start.strftime('%U')}.pptx"
                message_anomaly = message_anomaly + f" identified on Week {week_start.strftime('%U')}"
            else:
                raise ValueError(f'Invalid period - {period}')

            message = email_config.body.format(yesterday.strftime('%B %d %Y'), message_anomaly)

            if in_production:
                filepath = f"/tmp/{filename}"
            else:
                filepath = filename
            ppt.save(filepath)
            print(f"Saved {filepath}")
            if total_count > 0:
                # send_ppt_to_slack(filepath, message, location)
                if in_production:
                    send_mail(recipient=email_config.primary_email,
                              cc=email_config.cc,
                              subject=email_config.subject.format(yesterday.strftime('%B %d %Y')),
                              message=message,
                              filepath=filepath)
                    update_story_sent_info(project_id, dataset_id, cl_timezone,"true")
                    # update_story_sent_info(project_id, dataset_id, cl_timezone,"true")
                # else:
                    # send_mail(recipient = 'mohith.das@sarasanalytics.com, sai.harshith@sarasanalytics.com',
                    #           cc='srikar.kolli@sarasanalytics.com',
                    #           subject=email_config.subject.format(yesterday.strftime('%B %d %Y')),
                    #           message=message,
                    #           filepath=filepath)
            else:
                # send_ppt_to_slack(None, message, location)
                pass
    except Exception as e:
            update_story_sent_info(project_id, dataset_id, cl_timezone,"false")
            print(f"Error in function : Start-ALerts: {e}")
    



