#!/usr/bin/env python3

import os
import sys

import traceback

from lib_py3.common import remove_formatting
from lib_py3.item_replacement_rules import global_rules

class ItemReplacementManager(object):
    """
    A tool to replace items while preserving certain data.
    """
    def __init__(self,item_map):
        # Master copies
        self.item_map = item_map

        # Item pre/post-processing
        self.global_rules = global_rules

    def replace_item(self,item):
        """
        Replace an item per provided rules and master copy
        """
        # Abort replacement if the item has no ID (empty/invalid item) or no name (no valid replacement)
        if not ( item.has_path('id') and item.has_path('tag.display.Name') ):
            return

        # Get the correct replacement info; abort if none exists
        item_id = item.at_path('id').value
        item_name = remove_formatting(item.at_path('tag.display.Name').value)
        new_item_tag = self.item_map.get(item_id,{}).get(item_name,None)
        if not new_item_tag:
            return

        # Run preprocess rules; if one returns True, abort replacements on this item!
        for rule in self.global_rules:
            if rule.preprocess(item):
                return

        # Replace the item tag
        item.at_path('tag') = new_item_tag

        # Run postprocess rules
        for rule in self.global_rules:
            rule.postprocess(item)
