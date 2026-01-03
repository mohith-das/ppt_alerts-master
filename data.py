import os.path

from helper import get_anomaly_type, delta_pct, get_anomaly_df, get_table_details, check_critical, get_color, get_tables, check_warning, is_none
import numpy as np
import pandas as pd
from dates import yesterday, sdlw, current_date, get_previous_week_start_date_end_date, year_ago, six_months_ago, three_months_ago
from datetime import date, datetime, timedelta
from bigquery import get_bigquery_client


# year_ago = date.today() - timedelta(days=365)
# six_months_ago = date.today() - timedelta(days=6*30)
# three_months_ago = date.today() - timedelta(days=3*30)


def get_data_dict(asset, data_source, period, anomaly_df, metric, dimension=np.nan, dim_label=np.nan):

    if period == 'daily':
        date_col = 'Date'
        weekday = None
        current_date = yesterday.strftime('%Y-%m-%d')
        prev_date = sdlw.strftime('%Y-%m-%d')
    elif period == 'weekly':
        date_col = 'Week'
        weekday = pd.to_datetime(anomaly_df[date_col]).dt.weekday.iloc[0]
        week_start, week_end = get_previous_week_start_date_end_date(current_date, weekday=weekday)
        prev_week_start, prev_week_end = get_previous_week_start_date_end_date(week_start, weekday=weekday)
        current_date = week_start.strftime('%Y-%m-%d')
        prev_date = prev_week_start.strftime('%Y-%m-%d')
    else:
        raise Exception(f"Invalid period - {period}")

    anomaly_df[f'{metric}_yhat'] = np.maximum(anomaly_df[f'{metric}_yhat'], 0)
    anomaly_df[f'{metric}_yhat_upper'] = np.maximum(anomaly_df[f'{metric}_yhat_upper'], 0)
    anomaly_df[f'{metric}_yhat_lower'] = np.maximum(anomaly_df[f'{metric}_yhat_lower'], 0)

    not_null_mask = anomaly_df[metric].notnull()
    if anomaly_df[not_null_mask].shape[0] < 10: # Change to 15
        return

    current_date_mask = anomaly_df[date_col] == current_date
    current_value = anomaly_df[current_date_mask][metric].iloc[0]

    year_mask = (anomaly_df[date_col] >= year_ago.strftime('%Y-%m-%d')) & (anomaly_df[date_col] <= current_date)
    year_maximum = anomaly_df[year_mask][metric].max()
    is_year_maximum = current_value == year_maximum

    six_month_mask = (anomaly_df[date_col] >= six_months_ago.strftime('%Y-%m-%d')) & (anomaly_df[date_col] <= current_date)
    six_month_maximum = anomaly_df[six_month_mask][metric].max()
    is_six_month_maximum = current_value == six_month_maximum

    three_month_mask = (anomaly_df[date_col] >= three_months_ago.strftime('%Y-%m-%d')) & (anomaly_df[date_col] <= current_date)
    three_month_maximum = anomaly_df[three_month_mask][metric].max()
    is_three_month_maximum = current_value == three_month_maximum

    current_anomaly_df = anomaly_df[anomaly_df[date_col] == current_date]
    prev_anomaly_df = anomaly_df[anomaly_df[date_col] == prev_date]

    if not current_anomaly_df.empty:
        y = current_anomaly_df[metric].iloc[-1]
        yhat = current_anomaly_df[f'{metric}_yhat'].iloc[-1]
        yhat_upper = current_anomaly_df[f'{metric}_yhat_upper'].iloc[-1]
        yhat_lower = current_anomaly_df[f'{metric}_yhat_lower'].iloc[-1]
    else:
        y = 0
        yhat = prev_anomaly_df[f'{metric}_yhat'].iloc[-1]
        yhat_upper = prev_anomaly_df[f'{metric}_yhat_upper'].iloc[-1]
        yhat_lower = prev_anomaly_df[f'{metric}_yhat_lower'].iloc[-1]

    if prev_anomaly_df.empty:
        y_prev = 0
    else:
        y_prev = prev_anomaly_df[metric].iloc[-1]

    threshold = (yhat_upper - yhat_lower)/2
    y_prev_upper = y_prev + threshold
    y_prev_lower = y_prev - threshold

    anomaly_type = get_anomaly_type(y, upper=y_prev_upper, lower=y_prev_lower)
    yhat_anomaly_type = get_anomaly_type(y, upper=yhat_upper, lower=yhat_lower)
    is_anomaly = anomaly_type in [1, -1]
    # is_critical = check_critical(y, upper=y_prev_upper, lower=y_prev_lower)
    is_critical = check_critical(y, upper=yhat_upper, lower=yhat_lower)
    # is_warning = check_warning(y, upper=y_prev_upper, lower=y_prev_lower)
    is_warning = check_warning(y, upper=yhat_upper, lower=yhat_lower)

    data_dict = {
        'asset': asset,
        'data_source': data_source,
        'period': period,
        'weekday': weekday,
        'dimension': dimension,
        'dim_label': dim_label,
        'metric': metric,
        'y': y,
        'y_prev_lower': y_prev_lower,
        'y_prev_upper': y_prev_upper,
        'y_prev': y_prev,
        'yhat': yhat,
        'yhat_lower': yhat_lower,
        'yhat_upper': yhat_upper,
        'is_anomaly': is_anomaly,
        'is_warning': is_warning,
        'is_critical': is_critical,
        'anomaly_type': anomaly_type,
        'yhat_anomaly_type': yhat_anomaly_type,
        'color': get_color(anomaly_type, metric),
        'yhat_color': get_color(yhat_anomaly_type, metric),
        'is_year_maximum': is_year_maximum,
        'is_six_month_maximum': is_six_month_maximum,
        'is_three_month_maximum': is_three_month_maximum,
    }

    if period == 'daily':
        mask = three_month_mask & not_null_mask
    else:
        mask = six_month_mask & not_null_mask

    if period == 'weekly':
        data_dict['xaxis_data'] = anomaly_df[mask][date_col].apply(lambda d: f"W{datetime.strptime(d, '%Y-%m-%d').date().strftime('%U')}")
    else:
        data_dict['xaxis_data'] = anomaly_df[mask][date_col]
    data_dict['yaxis_data'] = anomaly_df[mask][metric]
    data_dict['trend_data'] = anomaly_df[mask][f'{metric}_trend']
    data_dict['yhat_data'] = anomaly_df[mask][f'{metric}_yhat']
    data_dict['yhat_upper_data'] = anomaly_df[mask][f'{metric}_yhat_upper']
    data_dict['yhat_lower_data'] = anomaly_df[mask][f'{metric}_yhat_lower']
    data_dict['yhat_anomaly_type_data'] = anomaly_df[mask].apply(lambda row: get_anomaly_type(y=row[metric], upper=row[f'{metric}_yhat_upper'], lower=row[f'{metric}_yhat_lower']), axis=1)

    return data_dict


def get_revenue_impact_for_row(row, asset_df):
    # print(row['data_source'], row['dimension'], row['dim_label'], row['metric'])

    is_subscription_type = 'New_Subscription' in asset_df['dim_label'].unique()

    if row['data_source'] == 'Google Ads':
        data_source_mask = asset_df['data_source'] == 'Google Analytics'
    elif row['data_source'] == 'Google Analytics' and is_none(row['dimension']):
        data_source_mask = asset_df['data_source'] == 'Ecommerce'
    else:
        data_source_mask = asset_df['data_source'] == row['data_source']

    if is_none(row['dimension']):
        if row['data_source'] == 'Google Ads':
            dimension_mask = asset_df['dimension'] == 'Source_medium'
        elif row['data_source'] == 'Facebook':
            dimension_mask = asset_df['dimension'].isnull()
        elif row['metric'] == 'Revenue':
            dimension_mask = asset_df['dimension'].isnull()
        elif row['metric'] == 'Cancelled_Subscriptions':
            dimension_mask = asset_df['dimension'] == 'User_Type'
        else:
            if is_subscription_type:
                dimension_mask = asset_df['dimension'] == 'User_Type'
            else:
                dimension_mask = asset_df['dimension'].isnull()
    else:
        dimension_mask = asset_df['dimension'] == row['dimension']

    if is_none(row['dim_label']):
        if row['data_source'] == 'Google Ads':
            dim_label_mask = asset_df['dim_label'] == 'google / cpc'
            # print('using google / cpc revenue')
        elif row['data_source'] == 'Facebook':
            dim_label_mask = asset_df['dim_label'].isnull()
        elif row['metric'] == 'Revenue':
            dim_label_mask = asset_df['dim_label'].isnull()
        elif row['metric'] == 'Cancelled_Subscriptions':
            dim_label_mask = asset_df['dim_label'] == 'New_Subscription'
            # print('using New_Subscription revenue')
        else:
            if is_subscription_type:
                dim_label_mask = asset_df['dim_label'] == 'New_Subscription'
            else:
                dim_label_mask = asset_df['dim_label'].isnull()
            # print('using New_Subscription revenue')
    else:
        dim_label_mask = asset_df['dim_label'] == row['dim_label']
        # print(f"using {row['dim_label']} revenue")

    revenue_mask = asset_df['metric'].isin(['Revenue', 'Gross_Revenue', 'Total_Sales', 'Ad_Sales'])

    filtered_df = asset_df[data_source_mask & dimension_mask & dim_label_mask & revenue_mask]
    if filtered_df.shape[0] > 1:
        raise ValueError(f'Error while calculating Revenue impact: More than one rows for row - {row}')
    elif filtered_df.empty:
        # print(f' No revenue impact for - {row}')
        return 0
    else:
        revenue = filtered_df['y'].iloc[0]
        revenue_yhat = filtered_df['yhat'].iloc[0]
        if revenue_yhat == 0:
            print('revenue_prev is 0')
            # print(revenue)
            return abs(revenue)
        else:
            if np.isinf(row['delta']) or row['metric'] in ['ACOS', 'Returns', 'Return_Quantity']:
            # if np.isinf(row['delta']):
                revenue_impact = revenue - revenue_yhat
            else:
                revenue_impact = revenue_yhat * row['delta']/100

            max_revenue_impact = (revenue - revenue_yhat) * 10
            # print(f"revenue_yhat is {revenue_yhat} delta is {row['delta']/100}")
            # print(abs(revenue_impact))
            return min(abs(revenue_impact), abs(max_revenue_impact))


def get_asset_df(account, project_id, dataset_id, period):
    errors = []
    # if not os.path.exists(file_pkl):

    asset_df = pd.DataFrame(
        columns=[
            'asset',
            'data_source',
            'period',
            'weekday',
            'dimension',
            'dim_label',
            'metric',
            'y',
            'y_prev',
            'yhat',
            'y_prev_lower',
            'y_prev_upper',
            'is_anomaly',
            'anomaly_type',
            'yhat_anomaly_type',
            'color',
            'is_year_maximum',
            'is_six_month_maximum',
            'is_three_month_maximum',
        ]
    )

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

    if asset_df.empty:
        return asset_df, errors

    asset_df['delta'] = asset_df.apply(lambda row: delta_pct(now=row['y'], prev=row['yhat']), axis=1)
    asset_df['abs_delta'] = asset_df['delta'].abs()

    asset_df['color'] = asset_df.apply(lambda row: get_color(row['anomaly_type'], row['metric']), axis=1)

    asset_df['revenue_impact'] = asset_df.apply(lambda row: get_revenue_impact_for_row(row, asset_df), axis=1)

    # asset_df.sort_values(by=['color', 'abs_delta'], ascending=False, inplace=True)
    asset_df.sort_values(by='revenue_impact', ascending=False, inplace=True)

    # data_source_mask = asset_df['data_source'] == 'Google Analytics'
    # dimension_mask = asset_df['dimension'].isnull()
    # dim_label_mask = asset_df['dim_label'].isnull()
    # metric_mask = asset_df['metric'] == 'Revenue'
    #
    # ga_revenue_mask = data_source_mask & dimension_mask & dim_label_mask & metric_mask
    #
    # asset_df = asset_df[~ga_revenue_mask]
    # asset_df.to_csv(file, index=False)
    # asset_df.to_pickle(file_pkl)
    # else:
    #     asset_df = pd.read_pickle(file_pkl)

    return asset_df, errors