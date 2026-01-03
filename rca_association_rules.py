from anytree import NodeMixin, RenderTree
import re


class AssociationTreeNode(NodeMixin):
    def __init__(self, id, data_source, dimension, dim_label, metric, parent=None, reverse_effect_on_parent=False, children=None, dim_labels_to_be_excluded=None, metrics_to_be_excluded=None):
        self.id, = id,
        self.data_source = data_source
        self.dimension = dimension
        self.dim_label = dim_label
        self.metric = metric
        self.name = f"{id} {data_source} {dimension} {dim_label} {metric}"
        self.parent = parent
        self.reverse_effect_on_parent = reverse_effect_on_parent
        self.printed = False
        self.dim_labels_to_be_excluded = dim_labels_to_be_excluded
        self.metrics_to_be_excluded = metrics_to_be_excluded
        if children:
            self.children = children


'''Ecommerce Tree'''
"""Old Rules"""
# n1 = AssociationTreeNode(id='n1', data_source='Ecommerce', dimension=None, dim_label=None, metric='Total_Sales')
# n2 = AssociationTreeNode(id='n2', data_source='Ecommerce', dimension=None, dim_label=None, metric='AOV', parent=n1)
# n3 = AssociationTreeNode(id='n3', data_source='Ecommerce', dimension=None, dim_label=None, metric='Orders', parent=n1)
# n4 = AssociationTreeNode(id='n4', data_source='mwsAds', dimension=None, dim_label=None, metric='Conversion_Rate', parent=n3)
# n5 = AssociationTreeNode(id='n5', data_source='mwsAds', dimension=None, dim_label=None, metric='Clicks', parent=n3)
# n6 = AssociationTreeNode(id='n6', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Spend', parent=n5)
# n7 = AssociationTreeNode(id='n7', data_source='mwsAds', dimension=None, dim_label=None, metric='ACOS', parent=n5)

"""New Rules"""
n1 = AssociationTreeNode(id='n1', data_source='Ecommerce', dimension=None, dim_label=None, metric='Total_Sales')
n2 = AssociationTreeNode(id='n2', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_Sales', parent=n1)
n3 = AssociationTreeNode(id='n3', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Sales', parent=n1)
n4 = AssociationTreeNode(id='n4', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_AOV', parent=n2)
n5 = AssociationTreeNode(id='n5', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_Orders', parent=n2)
n6 = AssociationTreeNode(id='n6', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_AOV', parent=n3)
n7 = AssociationTreeNode(id='n7', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Orders', parent=n3)
n8 = AssociationTreeNode(id='n8', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_Units_per_Order', parent=n4)
n9 = AssociationTreeNode(id='n9', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_Price_per_Unit', parent=n4)
n10 = AssociationTreeNode(id='n10', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_CVR', parent=n5)
n11 = AssociationTreeNode(id='n11', data_source='Ecommerce', dimension=None, dim_label=None, metric='Organic_Traffic', parent=n5)
n12 = AssociationTreeNode(id='n12', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Units_per_Order', parent=n6)
n13 = AssociationTreeNode(id='n13', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Price_per_Unit', parent=n6)
n14 = AssociationTreeNode(id='n14', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_CVR', parent=n7)
n15 = AssociationTreeNode(id='n15', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Traffic', parent=n7)
n16 = AssociationTreeNode(id='n16', data_source='Ecommerce', dimension='Promotions', dim_label='anything', metric='Total_Sales', parent=n15)
n17 = AssociationTreeNode(id='n17', data_source='mwsAds', dimension=None, dim_label=None, metric='ACOS', parent=n15)
n18 = AssociationTreeNode(id='n18', data_source='mwsAds', dimension=None, dim_label=None, metric='Ad_Spend', parent=n15)
n19 = AssociationTreeNode(id='n19', data_source='mwsAds', dimension='Ad_Type', dim_label='anything', metric='Ad_Spend', parent=n18)
n20 = AssociationTreeNode(id='n20', data_source='mwsAds', dimension='Campaign_Name', dim_label='anything', metric='Ad_Spend', parent=n18)
n21 = AssociationTreeNode(id='n22', data_source='mwsAds', dimension='ASIN', dim_label='anything', metric='Ad_Spend', parent=n18)
# n14 = AssociationTreeNode(id='n14', data_source='mwsAds', dimension=None, dim_label=None, metric='Discounts', parent=n10)
# n17 = AssociationTreeNode(id='n17', data_source='mwsAds', dimension=None, dim_label=None, metric='AdType', parent=n15)
# n18 = AssociationTreeNode(id='n18', data_source='mwsAds', dimension=None, dim_label=None, metric='Campaign', parent=n15)
# n19 = AssociationTreeNode(id='n19', data_source='mwsAds', dimension=None, dim_label=None, metric='Product', parent=n15)


association_rules_root_nodes = [n1]


print("Association rules -")
for pre, fill, node in RenderTree(n1):
    if node.reverse_effect_on_parent:
        print(f"{pre}{node.name} (Reverse)")
    else:
        print(f"{pre}{node.name}")
