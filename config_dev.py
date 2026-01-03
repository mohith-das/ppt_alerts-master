import os
from collections import defaultdict
from pptx.dml.color import RGBColor

WATCHDOG_PROJECT_ID = 'watchdog-340107'
config_dataset = 'config_dev'
config_table = 'account_assets_dev'
config_info_table = 'dev_account_asset_info'
table_suffix = '_anomaly_dev'
function_name = 'dev_ppt_alerts'
log_table = 'dev_execution_log'

TEST_WEBHOOK = os.getenv('TEAMS_WEBHOOK_URL', 'replace_teams_webhook')

LEVIS_WEBHOOK = os.getenv('LEVIS_WEBHOOK_URL', '')

REVERSE_METRICS = [
    'bounce_rate',
    'ship_time',
    'click_to_delivery_time',
    'cancelled_subscriptions',
    'cpc',
    'orders_returned',
    'refund_amount',
    'acos',
    'returns',
    'return_quantity',
    'return_rate'
]

in_production = os.getenv('GCP_PROJECT')
# in_production = 0
# in_production = 1

currency_dict = {'ph': '₱',
                 'ml': 'RM',
                 'indo': 'Rp',
                 'aus_nz': 'AUD',
                 'kr': 'KRW',
                 'jp': 'JPY',
                 'japan': 'JPY'
                 }


class Kpi:
    def __init__(self, data_source, dimension, dim_label, metric):
        self.data_source = data_source
        self.dimension = dimension
        self.dim_label = dim_label
        self.metric = metric
        self.xaxis_data = None
        self.yaxis_data = None


default_kpi_list = [
        Kpi('Google Analytics', None, None, 'Revenue'),
        Kpi('Google Analytics', None, None, 'Orders'),
        Kpi('Google Analytics', None, None, 'Conversion_Rate'),
        Kpi('Google Analytics', None, None, 'AOV'),
]

kpi_list_dict = defaultdict(lambda: default_kpi_list)

kpi_list_dict['Levis'] = [
        Kpi('Google Analytics', None, None, 'Revenue'),
        Kpi('Google Analytics', None, None, 'Traffic'),
        Kpi('Google Analytics', None, None, 'Conversion_Rate'),
        Kpi('Google Analytics', None, None, 'Orders'),
        Kpi('Google Analytics', None, None, 'Page_Views'),
        Kpi('Google Analytics', None, None, 'Bounce_Rate'),
        Kpi('Google Analytics', None, None, 'AOV'),
        Kpi('Google Analytics', None, None, 'Transactions'),
        Kpi('Google Analytics', None, None, 'Avg_Session_Duration'),
        Kpi('Google Analytics', None, None, 'Sessions'),
        Kpi('capillary', None, None, 'Revenue'),
        Kpi('capillary', None, None, 'Orders'),
        Kpi('capillary', None, None, 'Units'),
        Kpi('capillary', None, None, 'AOV'),
        Kpi('capillary', None, None, 'UPT'),
        Kpi('capillary', None, None, 'AUR'),
        Kpi('capillary', None, None, 'Returns'),
        Kpi('capillary', None, None, 'Return_Quantity'),
        Kpi('capillary', None, None, 'Revenue_Share'),
        Kpi('capillary', None, None, 'Order_Share'),
        Kpi('capillary', None, None, 'Revenue_Mix'),
        Kpi('capillary', None, None, 'Quantity')
]


class Email:
    def __init__(self, asset_name, primary_email, cc, client_timezone):
        self.asset_name = asset_name
        self.primary_email = primary_email
        self.cc = cc
        self.client_timezone = client_timezone
        self.subject = "Anomaly Alerts {} " + self.asset_name
        name = f"{primary_email[0].upper()}{primary_email.split('@')[0][1:]}"
        self.body = """Hello,\n""" + \
                    """Please find attached copy of Anomaly Alerts generated for """ + f"{self.asset_name}" + \
                    """ for {}.\n\n
                       {}\n\n
                       Kindly reach out to us in case of further queries.\n
                       Regards,
                       Watchdog Team
                       Saras Analytics."""


# primary_email = "srikar.kolli@sarasanalytics.com,santosh.nanduru@sarasanalytics.com," \
#                 "sumaya.bai@sarasanalytics.com,saikiran.kallem@sarasanalytics.com"
primary_email = 'srikar.kolli@sarasanalytics.com,santosh.nanduru@sarasanalytics.com,saikiran.kallem@sarasanalytics.com,' \
                'sumaya.bai@sarasanalytics.com'
# primary_email = 'srikar.kolli@sarasanalytics.com,sumaya.bai@sarasanalytics.com'
#
dict_email_config = {'Levis SG': Email(asset_name="Levis Singapore",
                                      primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                       client_timezone='Asia/Singapore'),
                     'Levis Malaysia': Email(asset_name="Levis Malaysia",
                                             primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                             client_timezone='Asia/Jakarta'),
                     'Levis Indonesia': Email(asset_name="Levis Indonesia",
                                              primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                              client_timezone=''),
                     'Levis Philippines': Email(asset_name="Levis Philippines",
                                               primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                                client_timezone='Asia/Manila'),
                     'Levis AUS_NZ': Email(asset_name="Levis Australia & New Zealand",
                                           primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                           client_timezone='Australia/Canberra'),
                     'Levis Korea': Email(asset_name="Levis Korea",
                                          primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                          client_timezone='Asia/Seoul'),
                     'Levis JP': Email(asset_name="Levis Japan",
                                       primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                       client_timezone='Asia/Tokyo'),
                     'Levis Japan': Email(asset_name="Levis Japan",
                                          primary_email=primary_email,
                                          cc="",
                                          client_timezone='Asia/Tokyo'),
                       'Levis PH 24': Email(asset_name="Levis PH 24",
                                          primary_email="mohith.das@sarasanalytics.com,sai.harshith@sarasanalytics.com",
                                          cc="",
                                          client_timezone='Asia/Manila')
                #                           ,
                #      'Test': Email(asset_name="Test",
                #                           primary_email="mohith.das@sarasanalytics.com",
                #                           cc="sai.harshith@sarasanalytics.com")
                     }

# dict_email_config = {'Levis AUS_NZ': Email(asset_name="Levis Australia & New Zealand",
#                                            primary_email=primary_email,
#                                            cc="")}
        #'Levis SG': Email(asset_name="Levis Singapore",
#                                        primary_email=primary_email,
#                                        cc=""),
#                      'Levis Malaysia': Email(asset_name="Levis Malaysia",
#                                              primary_email=primary_email,
#                                              cc=""),
#                      'Levis Indonesia': Email(asset_name="Levis Indonesia",
#                                               primary_email=primary_email,
#                                               cc=""),
#                      'Levis Philippines': Email(asset_name="Levis Philippines",
#                                                 primary_email=primary_email,
#                                                 cc=""),
#                      }

color_dict = {'red1': RGBColor(229, 88, 1), 'red2': RGBColor(192, 0, 0),
              'green1': RGBColor(0, 220, 0), 'green2': RGBColor(0, 200, 0),
              'grey': RGBColor(172, 172, 172)}
