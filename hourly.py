import os
import numpy as np
import pandas as pd
from config import in_production
from graph import get_graph
from helper import get_tables, get_anomaly_df, get_table_details, get_anomaly_type, print_delta, print_formatted
from helper import check_critical, get_color, get_bigquery_client, delta_pct, not_none, fix_name
from data import get_revenue_impact_for_row
from datetime import date, timedelta
from slack_sdk import WebClient

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "replace_slack_bot_token")
from dates import year_ago, six_months_ago, three_months_ago, hourly_date_start


# year_ago = date.today() - timedelta(days=365)
# six_months_ago = date.today() - timedelta(days=6*30)
# three_months_ago = date.today() - timedelta(days=3*30)
# hourly_date_start = date.today() - timedelta(days=3)


def get_data_dict(asset, data_source, period, anomaly_df, metric, dimension=np.nan, dim_label=np.nan):

    date_col = 'DateHour'

    not_null_mask = anomaly_df[metric].notnull()

    WINDOW = 3

    anomaly_df[f'{metric}_yhat'] = np.maximum(anomaly_df[f'{metric}_yhat'], 0)
    anomaly_df[f'{metric}_yhat_upper'] = np.maximum(anomaly_df[f'{metric}_yhat_upper'], 0)
    anomaly_df[f'{metric}_yhat_lower'] = np.maximum(anomaly_df[f'{metric}_yhat_lower'], 0)

    anomaly_df['percentile'] = anomaly_df[f'{metric}_yhat'].rank(pct=True)

    current_anomaly_df = anomaly_df[not_null_mask].iloc[-WINDOW:]
    current_anomaly_df['yhat_anomaly_type'] = current_anomaly_df.apply(lambda row: get_anomaly_type(y=row[metric], upper=row[f'{metric}_yhat_upper'], lower=row[f'{metric}_yhat_lower']), axis=1)
    prev_anomaly_df = anomaly_df[not_null_mask].iloc[:-WINDOW]
    prev_anomaly_df['yhat_anomaly_type'] = prev_anomaly_df.apply(lambda row: get_anomaly_type(y=row[metric], upper=row[f'{metric}_yhat_upper'], lower=row[f'{metric}_yhat_lower']), axis=1)

    anomaly_sum = current_anomaly_df['yhat_anomaly_type'].sum()
    is_yhat_anomaly = abs(anomaly_sum) == WINDOW

    y = current_anomaly_df[metric].mean()
    yhat = current_anomaly_df[f'{metric}_yhat'].mean()
    yhat_upper = current_anomaly_df[f'{metric}_yhat_upper'].mean()
    yhat_lower = current_anomaly_df[f'{metric}_yhat_lower'].mean()

    if current_anomaly_df['percentile'].min() < 0.4:
        business_filter = False
    else:
        business_filter = True
        
    yhat_anomaly_type = anomaly_sum // WINDOW if is_yhat_anomaly and business_filter else 0

    current_anomaly_df['is_yhat_critical'] = current_anomaly_df.apply(lambda row: check_critical(y=row[metric], upper=row[f'{metric}_yhat_upper'], lower=row[f'{metric}_yhat_lower'], threshold=20), axis=1)

    is_yhat_critical = current_anomaly_df['is_yhat_critical'].sum() // WINDOW if is_yhat_anomaly and business_filter else 0

    # is_yhat_critical = check_critical(y, upper=yhat_upper, lower=yhat_lower, threshold=20) if is_yhat_anomaly and business_filter else False
    # is_yhat_warning = check_warning(y, upper=yhat_upper, lower=yhat_lower) if is_yhat_anomaly and business_filter else False

    data_dict = {
        'asset': asset,
        'data_source': data_source,
        'period': period,
        'dimension': dimension,
        'dim_label': dim_label,
        'metric': metric,
        'y': y,
        'yhat': yhat,
        'yhat_lower': yhat_lower,
        'yhat_upper': yhat_upper,
        'is_yhat_anomaly': is_yhat_anomaly,
        # 'is_yhat_warning': is_yhat_warning,
        'is_yhat_critical': is_yhat_critical,
        'yhat_anomaly_type': yhat_anomaly_type,
        'yhat_color': get_color(yhat_anomaly_type, metric),
    }

    mask = anomaly_df[date_col] >= hourly_date_start.strftime('%Y-%m-%d')

    data_dict['xaxis_data'] = anomaly_df[mask][date_col]
    data_dict['yaxis_data'] = anomaly_df[mask][metric]
    data_dict['trend_data'] = anomaly_df[mask][f'{metric}_trend']
    data_dict['yhat_data'] = anomaly_df[mask][f'{metric}_yhat']
    data_dict['yhat_upper_data'] = anomaly_df[mask][f'{metric}_yhat_upper']
    data_dict['yhat_lower_data'] = anomaly_df[mask][f'{metric}_yhat_lower']
    data_dict['yhat_anomaly_type_data'] = anomaly_df[mask].apply(lambda row: get_anomaly_type(y=row[metric], upper=row[f'{metric}_yhat_upper'], lower=row[f'{metric}_yhat_lower']), axis=1)

    return data_dict


def get_hourly_asset_df(account, project_id, dataset_id):
    errors = []

    asset_df = pd.DataFrame(
        columns=[
            'asset',
            'data_source',
            'period',
            'dimension',
            'dim_label',
            'metric',
            'y',
            'yhat',
            'is_anomaly',
            'yhat_anomaly_type',
            'yhat_color',
            'is_yhat_warning',
            'is_yhat_critical',
        ]
    )

    period = 'hourly'

    table_ids = get_tables(project_id, dataset_id, period)

    for table_id in table_ids:
        try:
            anomaly_df = get_anomaly_df(project_id, dataset_id, table_id, period)
        except Exception as e:
            error_msg = f"Error while getting data for - {project_id} {dataset_id} {table_id} : {e}"
            print(error_msg)
            errors.append(error_msg)
            continue

        data_source, dim, metrics = get_table_details(project_id, dataset_id, table_id)

        if dim is None:
            for metric in metrics:
                try:
                    data_dict = get_data_dict(dataset_id, data_source, period, anomaly_df, metric)
                except Exception as e:
                    error_msg = f"Error while getting yesterday data for dataset_id-{dataset_id} data_source-{data_source} metric-{metric} : {e}"
                    print(error_msg)
                    errors.append(error_msg)
                    continue
                else:
                    asset_df = asset_df.append(data_dict, ignore_index=True)

        else:
            groups = anomaly_df.groupby(dim)
            for dim_label, group_df in groups:
                for metric in metrics:
                    try:
                        data_dict = get_data_dict(dataset_id, data_source, period, group_df, metric, dim, dim_label)
                    except Exception as e:
                        error_msg = f"Error while getting yesterday data for dataset_id-{dataset_id} data_source-{data_source} dimension-{dim} dim_label-{dim_label} metric-{metric} : {e}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue
                    else:
                        asset_df = asset_df.append(data_dict, ignore_index=True)

    asset_df['delta'] = asset_df.apply(lambda row: delta_pct(now=row['y'], prev=row['yhat']), axis=1)
    asset_df['abs_delta'] = asset_df['delta'].abs()

    asset_df['yhat_color'] = asset_df.apply(lambda row: get_color(row['yhat_anomaly_type'], row['metric']), axis=1)

    asset_df['revenue_impact'] = asset_df.apply(lambda row: get_revenue_impact_for_row(row, asset_df), axis=1)

    # asset_df.sort_values(by=['color', 'abs_delta'], ascending=False, inplace=True)
    asset_df.sort_values(by='revenue_impact', ascending=False, inplace=True)

    data_source_mask = asset_df['data_source'] == 'Google Analytics'
    dimension_mask = asset_df['dimension'].isnull()
    dim_label_mask = asset_df['dim_label'].isnull()
    metric_mask = asset_df['metric'] == 'Revenue'

    ga_revenue_mask = data_source_mask & dimension_mask & dim_label_mask & metric_mask

    asset_df = asset_df[~ga_revenue_mask]

    return asset_df, errors


def create_chart(row):
    metric = row['metric']
    xaxis_data = row['xaxis_data']
    yaxis_data = row['yaxis_data']
    trend_data = row['trend_data']
    yhat_upper_data = row['yhat_upper_data']
    yhat_lower_data = row['yhat_lower_data']
    anomaly_type_data = row['yhat_anomaly_type_data']
    fig = get_graph(metric, xaxis_data, yaxis_data, trend_data, yhat_upper_data, yhat_lower_data, anomaly_type_data)
    img_path = "/tmp/anomaly.png" if in_production else "anomaly.png"
    fig.write_image(img_path, width=536, height=362)

    return img_path


def send_hourly_alerts(project_id, account, location):

    client = get_bigquery_client(project_id='watchdog-340107')

    query = f"SELECT * FROM `watchdog-340107.config.account_assets` WHERE account = '{account}' ORDER BY sequence_no"
    dataset_df = (
        client.query(query)
            .result()
            .to_dataframe()
    )

    print("Got list of assets")

    client = WebClient(token=SLACK_BOT_TOKEN)

    location = '#watchdog-test'

    if not in_production:
        location = 'wdt2'

    for i, row in dataset_df.iterrows():
        if row['dataset_id'] != 'Overall':
            hourly_asset_df, errors = get_hourly_asset_df(account, project_id, row['dataset_id'])
            for i, row in hourly_asset_df.iterrows():
                # if (row['is_yhat_warning'] or row['is_yhat_critical']):
                if row['is_yhat_critical']:
                    forecast_comment = f"{fix_name(row['asset'])} - {'Warning' if row['is_yhat_warning'] else ':bangbang:Critical'} -"
                    if not_none(row['dim_label']):
                        forecast_comment = forecast_comment + f" {fix_name(row['dim_label'])}"
                    forecast_comment = forecast_comment + f" {fix_name(row['metric'])} ({print_formatted(row['y'], row['metric'])})"
                    if row['metric'].endswith('s'):
                        forecast_comment = forecast_comment + " are"
                    else:
                        forecast_comment = forecast_comment + " is"

                    forecast_comment = forecast_comment + f" {print_delta(now=row['y'], prev=row['yhat'])}"

                    if row['y'] > row['yhat']:
                        forecast_comment = forecast_comment + " higher than"
                    else:
                        forecast_comment = forecast_comment + " lower than"

                    forecast_comment = forecast_comment + f" expected value of ({print_formatted(row['yhat'], row['metric'])})"

                    filepath = create_chart(row)

                    response = client.files_upload(channels=location, file=filepath, initial_comment=forecast_comment)
