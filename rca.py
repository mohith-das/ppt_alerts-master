from helper import print_anomaly, check_warning, check_critical, Element, DoubleStyle, print_orders, print_sales, \
                   is_none
from anytree import NodeMixin, RenderTree
from rca_association_rules import association_rules_root_nodes
import re
import itertools
from collections import defaultdict
from pptx.util import Pt
from pptx.dml.color import RGBColor


class Node(NodeMixin):
    def __init__(self, y, y_prev, yhat, yhat_upper, yhat_lower, anomaly_type, is_warning, is_critical, data_source, period, dimension, dim_label, metric, revenue_impact, parent=None, reverse_effect_on_parent=False, children=None):
        self.y = y
        self.y_prev = y_prev
        self.yhat = yhat
        self.yhat_upper = yhat_upper
        self.yhat_lower = yhat_lower
        self.anomaly_type = anomaly_type
        self.data_source = data_source
        self.period = period
        self.dimension = dimension
        self.dim_label = dim_label
        self.metric = metric
        self.revenue_impact = revenue_impact
        self.parent = parent
        self.reverse_effect_on_parent = reverse_effect_on_parent
        self.printed = False
        self.is_anomaly = anomaly_type in [1, -1]
        self.is_warning = is_warning
        self.is_critical = is_critical
        if children:
            self.children = children

    def __repr__(self):
        return f"Node({self.data_source}: {self.metric})"


def filter_data_by_association_rules_node(asset_df, association_rules_node, parent_node=None):
    if association_rules_node.data_source == 'same_as_parent':
        data_source_mask = asset_df['data_source'] == parent_node.data_source
    else:
        data_source_mask = asset_df['data_source'] == association_rules_node.data_source

    if association_rules_node.dimension:
        if association_rules_node.dimension == 'same_as_parent':
            dimension_mask = asset_df['dimension'] == parent_node.dimension
        else:
            dimension_mask = asset_df['dimension'] == association_rules_node.dimension
    else:
        dimension_mask = asset_df['dimension'].isnull()

    if isinstance(association_rules_node.metric, re.Pattern):
        metric_mask = asset_df['metric'].str.match(association_rules_node.metric)
    else:
        metric_mask = asset_df['metric'] == association_rules_node.metric

    if association_rules_node.dim_label:
        if association_rules_node.dim_label == 'anything':
            ads_sum = asset_df[dimension_mask & metric_mask].revenue_impact.sum()
            dim_label_check = asset_df[dimension_mask & metric_mask].revenue_impact.nlargest(3) if ads_sum > 0 \
                              else asset_df[dimension_mask & metric_mask].revenue_impact.nsmallest(n=3)
            dim_label_mask = asset_df['revenue_impact'].isin(dim_label_check)
        elif isinstance(association_rules_node.dim_label, re.Pattern):
            dim_label_mask = asset_df['dim_label'].str.match(association_rules_node.dim_label)
        elif association_rules_node.dim_label == 'same_as_parent':
            dim_label_mask = asset_df['dim_label'] == parent_node.dim_label
        else:
            dim_label_mask = asset_df['dim_label'] == association_rules_node.dim_label
    else:
        dim_label_mask = asset_df['dim_label'].isnull()

    if association_rules_node.dim_labels_to_be_excluded:
        exclude_dim_labels_mask = asset_df['dim_label'].isin(association_rules_node.dim_labels_to_be_excluded)
    else:
        exclude_dim_labels_mask = False

    if association_rules_node.metrics_to_be_excluded:
        exclude_metrics_mask = asset_df['metric'].isin(association_rules_node.metrics_to_be_excluded)
    else:
        exclude_metrics_mask = False

    filtered_df = asset_df[data_source_mask & dimension_mask & dim_label_mask & metric_mask & ~exclude_dim_labels_mask & ~exclude_metrics_mask]
    return filtered_df


def get_nodes_from_df(filtered_df):
    nodes_list = []
    for index, row in filtered_df.iterrows():
        y = row['y']
        y_prev = row['y_prev']
        yhat = row['yhat']
        y_prev_lower = row['y_prev_lower']
        y_prev_upper = row['y_prev_upper']
        yhat_upper = row['yhat_upper']
        yhat_lower = row['yhat_lower']
        data_source = row['data_source']
        period = row['period']
        dimension = row['dimension']
        dim_label = row['dim_label']
        metric = row['metric']
        anomaly_type = row['yhat_anomaly_type']
        revenue_impact = row['revenue_impact']
        # is_critical = check_critical(y, upper=y_prev_upper, lower=y_prev_lower)
        is_critical = check_critical(y, upper=yhat_upper, lower=yhat_lower)
        is_warning = check_warning(y, upper=yhat_upper, lower=yhat_lower)
        node = Node(y, y_prev, yhat, yhat_upper, yhat_lower, anomaly_type, is_warning, is_critical, data_source, period, dimension, dim_label, metric, revenue_impact)
        nodes_list.append(node)

    nodes_list = sorted(nodes_list, key=lambda node: abs(node.revenue_impact), reverse=True)

    return nodes_list


def build_tree_with_all_metrics(asset_df, association_rules_node, parent_node=None, parent_association_rules_node=None):
    if parent_node:
        filtered_df = filter_data_by_association_rules_node(asset_df, association_rules_node, parent_node)
    else:
        filtered_df = filter_data_by_association_rules_node(asset_df, association_rules_node, parent_node=parent_association_rules_node)

    root_nodes_list = get_nodes_from_df(filtered_df)

    # if data is not available for the root nodes
    if not root_nodes_list:
        'create root nodes from the children'
        for association_rules_child in association_rules_node.children:
            root_nodes_list = build_tree_with_all_metrics(asset_df, association_rules_child, parent_node, association_rules_node)
            for root_node in root_nodes_list:
                root_node.parent = parent_node
        return root_nodes_list

    else:
        for root_node in root_nodes_list:
            for association_rules_child in association_rules_node.children:
                child_nodes_list = build_tree_with_all_metrics(asset_df, association_rules_child, root_node, association_rules_node)
                for child_node in child_nodes_list:
                    child_node.parent = root_node

        if association_rules_node.reverse_effect_on_parent:
            for node in root_nodes_list:
                node.reverse_effect_on_parent = True

    return root_nodes_list


# nodes_list = rca_nodes_list
# node = nodes_list[0]
def keep_only_anomalies(nodes_list, parent_anomaly_type=None):
    if not nodes_list:
        return []

    processed_nodes_list = []
    for node in nodes_list:
        same_anomaly_as_parent = (parent_anomaly_type == node.anomaly_type) and not node.reverse_effect_on_parent
        reverse_effect_on_parent = (parent_anomaly_type == -node.anomaly_type) and node.reverse_effect_on_parent
        node_explains_parent_anomaly = same_anomaly_as_parent or reverse_effect_on_parent

        if parent_anomaly_type is None:
            if node.is_anomaly:
                processed_nodes_list.append(node)
                node.children = keep_only_anomalies(node.children, node.anomaly_type)
            else:
                pass
        else:
            if node_explains_parent_anomaly:
                processed_nodes_list.append(node)
                # Only drill down to further levels in case of an anomaly at parent
                include_children = False
                if node.parent.parent:
                    if node.parent.parent.is_critical:
                        include_children = True
                else:
                    include_children = True
                if include_children:
                    node.children = keep_only_anomalies(node.children, node.anomaly_type)
            elif node.reverse_effect_on_parent:
                processed_children_list = keep_only_anomalies(node.children, -parent_anomaly_type)
                # Only drill down to further levels in case of an anomaly at parent
                include_children = False
                if node.parent.parent:
                    if node.parent.parent.is_critical:
                        include_children = True
                else:
                    include_children = True
                if include_children:
                    node.children = keep_only_anomalies(node.children, node.anomaly_type)
                processed_nodes_list.extend(processed_children_list)
            else:
                pass

    return processed_nodes_list


def print_tree_from_node(input_node, p, client_name, asset_df):
    style = DoubleStyle()
    if input_node and input_node.children and not input_node.printed:
        for pre, fill, node in RenderTree(input_node, style=DoubleStyle):
            node.printed = True
            print(node)
            # if node.metric in ['Clicks', 'Ad_Spend', 'ACOS'] and is_none(node.dimension):
            #     pre = style.empty + pre
            print_anomaly(p, node, pre)
            # if node.metric == 'Orders' and client_name in orders_df.client_name.unique():
            #     print_sales(client_name, asset_df, orders_df, p)
            # elif node.metric == 'Ad_Sales' and client_name in orders_df.client_name.unique():
            #     print_orders(client_name, orders_df, asset_df, p, orders_type="Ad")


def print_revenue_rca(asset_df, p):
    rca_nodes_list = build_tree_with_all_metrics(asset_df, association_rules_root_nodes[0])
    # rca_nodes_list = keep_only_anomalies(rca_nodes_list)
    client_name = asset_df.asset.values[-1]
    for root_node in rca_nodes_list:
        run = p.add_run()
        run.text = 'RCA:\n'
        font = run.font
        font.name = 'Poppins'
        font.size = Pt(18)
        font.bold = True
        font.color.rgb = RGBColor(70, 177, 255)
        # if not is_none(root_node.y):
        print_tree_from_node(root_node, p, client_name, asset_df)
        # else:
        #     run = p.add_run()
        #     run.text = f'\nData not available for {root_node.metric}'
        #     font = run.font
        #     font.name = 'Poppins'
        #     font.size = Pt(12)
        #     font.bold = True
        #     font.color.rgb = RGBColor(100, 100, 100)
