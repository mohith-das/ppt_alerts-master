from pptx import Presentation
from pptx.util import Inches
from bigquery import get_bigquery_client
from data import get_asset_df
from kpi_slide import add_kpi_slide
from anomaly_slide import add_anomaly_slide
from config import kpi_list_dict, dict_email_config, config_dataset, config_table
from dates import init_time


BASE_FONT_SIZE = 18


def new_ppt():
    ppt = Presentation()
    ppt.slide_width = Inches(13.1)
    ppt.slide_height = Inches(7.5)

    return ppt


def get_anomaly_type_counts(asset_df):
    negative_mask = asset_df['yhat_color'] == 'red'
    warning_mask = asset_df['is_warning']
    critical_mask = asset_df['is_critical']

    negative_warning_count = asset_df[negative_mask & warning_mask].shape[0]
    negative_critical_count = asset_df[negative_mask & critical_mask].shape[0]

    return negative_warning_count, negative_critical_count


def add_asset_slides(ppt, account, project_id, dataset_id, asset, period):
    print(f"\n\nGetting data for {asset}...")
    asset_df, errors = get_asset_df(account, project_id, dataset_id, period)

    if asset_df.empty:
        print(f"asset_df is empty for {account} {asset}")
        return 0, 0, 0

    print(f"Got data for {asset}")

    kpi_list = kpi_list_dict[account]
    if period == 'weekly':
        add_kpi_slide(ppt, period, asset, asset_df, kpi_list)

    negative_warning_count = 0
    negative_critical_count = 0
    total_count = 0

    print(f"\n\nPreparing anomaly slide for {asset}...")
    w, c, t = add_anomaly_slide(ppt, period, asset, asset_df, kpi_list)
    negative_warning_count += w
    negative_critical_count += c
    total_count += t
    # add_rca(ppt, period, asset_df)

    return negative_warning_count, negative_critical_count, total_count


def create_ppt(project_id, account, period, asset):

    client = get_bigquery_client(project_id='watchdog-340107')

    query = f"SELECT * FROM `watchdog-340107.{config_dataset}.{config_table}` WHERE account = '{account}' ORDER BY sequence_no"
    dataset_df = (
        client.query(query)
            .result()
            .to_dataframe()
    )
    
    dataset_df = dataset_df[dataset_df.dataset_id != "levis_jp_watchdog"].copy()
    # query_failsafe = f"SELECT * FROM `watchdog-340107.config.fail_safe_view` WHERE account = '{account}'"
    # fail_safe_df = client.query(query_failsafe).result().to_dataframe()
    # fail_df = fail_safe_df[fail_safe_df.fail_safe_available & ~fail_safe_df.datasets_updated]
    # if len(fail_df) > 0:
    #     dataset_df = dataset_df[~dataset_df.dataset_id.isin(fail_df.dataset_id.unique())]

    if asset != 'all':
        dataset_df = dataset_df[dataset_df.asset == asset]
        print(f'filtered for asset : {asset}')

    print("Got list of assets")

    dict_ppts = {}
    dict_neg_warn_count = {}
    dict_neg_crit_count = {}
    dict_tot_count = {}
    for i, row in dataset_df.iterrows():

        ppt = new_ppt()
        if asset == 'all':
            init_time(dict_email_config[row['asset']].client_timezone)
        w, c, t = add_asset_slides(ppt, account, project_id, dataset_id=row['dataset_id'], asset=row['asset'], period=period)
        dict_neg_warn_count[row['asset']] = w
        dict_neg_crit_count[row['asset']] = c
        dict_tot_count[row['asset']] = t
        dict_ppts[row['asset']] = ppt

    return dict_ppts, dict_neg_warn_count, dict_neg_crit_count, dict_tot_count
    # , fail_df
