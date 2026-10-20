"""Operations for transforming in-memory metadata trees."""

import copy
import re

import fmf.context
import fmf.utils as utils


class Merger:
    """Apply merge operators independently of the metadata tree."""

    def merge(self, data, source, name='/'):
        for key, value in source.items():
            if key.endswith('+'):
                self._plus(data, key.rstrip('+'), value, name=name)
            elif key.endswith('+<'):
                self._plus(data, key.rstrip('+<'), value, prepend=True, name=name)
            elif key.endswith('-~'):
                self._minus_regexp(data, key.rstrip('-~'), value, name=name)
            elif key.endswith('-'):
                self._minus(data, key.rstrip('-'), value, name=name)
            elif key.endswith('~'):
                self._regexp(data, key.rstrip('~'), value, name=name)
            else:
                data[key] = value
        return data

    def _plus(self, data, key, value, prepend=False, name='/'):
        if key not in data:
            data[key] = value
            return
        if isinstance(data[key], list) and isinstance(value, dict):
            for item in data[key]:
                if not isinstance(item, dict):
                    raise utils.MergeError("MergeError: Item '{0}' in {1} must be a dictionary."
                                           .format(item, name))
                self.merge(item, value, name)
            return
        if isinstance(data[key], dict) and isinstance(value, list):
            result = []
            for item in value:
                if not isinstance(item, dict):
                    raise utils.MergeError("MergeError: Item '{0}' in {1} must be a dictionary."
                                           .format(item, name))
                merged = copy.deepcopy(data[key])
                self.merge(merged, item, name)
                result.append(merged)
            data[key] = result
            return
        if isinstance(data[key], dict) and isinstance(value, dict):
            self.merge(data[key], value, name)
            return
        try:
            data[key] = value + data[key] if prepend else data[key] + value
        except TypeError as error:
            raise utils.MergeError("MergeError: Key '{0}' in {1} ({2}).".format(key, name, error))

    def _regexp(self, data, key, value, name='/'):
        if key not in data:
            return
        if isinstance(value, str):
            value = [value]
        for pattern, replacement in [utils.split_pattern_replacement(v) for v in value]:
            if isinstance(data[key], list):
                try:
                    data[key] = [re.sub(pattern, replacement, item) for item in data[key]]
                except TypeError:
                    raise utils.MergeError("MergeError: Key '{0}' in {1} (not a string)."
                                           .format(key, name))
            elif isinstance(data[key], str):
                data[key] = re.sub(pattern, replacement, data[key])
            else:
                raise utils.MergeError("MergeError: Key '{0}' in {1} (wrong type)."
                                       .format(key, name))

    def _minus_regexp(self, data, key, value, name='/'):
        if key not in data:
            return
        if isinstance(value, str):
            value = [value]

        def matches(item):
            return any(re.search(pattern, str(item)) for pattern in value)

        if isinstance(data[key], list):
            data[key] = [item for item in data[key] if not matches(item)]
        elif isinstance(data[key], str):
            if matches(data[key]):
                data[key] = ''
        elif isinstance(data[key], dict):
            for item in list(data[key]):
                if matches(item):
                    data[key].pop(item)
        else:
            raise utils.MergeError("MergeError: Key '{0}' in {1} (wrong type).".format(key, name))

    def _minus(self, data, key, value, name='/'):
        if key not in data:
            return
        if isinstance(data[key], (int, float)) and isinstance(value, (int, float)):
            data[key] -= value
        elif isinstance(data[key], str) and isinstance(value, str):
            data[key] = re.sub(value, '', data[key])
        elif isinstance(data[key], list) and isinstance(value, list):
            data[key] = [item for item in data[key] if item not in value]
        elif isinstance(data[key], dict) and isinstance(value, list):
            for item in value:
                data[key].pop(item, None)
        else:
            raise utils.MergeError("MergeError: Key '{0}' in {1} (wrong type).".format(key, name))


ADJUST_CONTROL_KEYS = ['because', 'continue', 'when']


class Adjuster:
    """Transform an already loaded tree for a particular context."""

    def __init__(self, merger=None):
        self.merger = merger or Merger()

    def adjust(self, node, context, key='adjust', undecided='skip',
               case_sensitive=None, decision_callback=None, additional_rules=None,
               additional_rules_callback=None):
        """Apply adjustment rules to ``node`` and all its descendants."""
        if not isinstance(context, fmf.context.Context):
            raise utils.GeneralError(
                "Invalid adjust context: '{}' .".format(type(context).__name__))

        if case_sensitive is not None:
            context._context_dimensions._default_dimension_cls.case_sensitive = case_sensitive

        try:
            rules = node.data[key]
            if isinstance(rules, dict):
                rules = [rules]
            if not isinstance(rules, list):
                raise utils.FormatError(
                    "Invalid adjust rule format in '{}'. Should be a dictionary or a list "
                    "of dictionaries, got '{}' .".format(node.name, type(rules).__name__))
        except KeyError:
            rules = []

        if additional_rules is None:
            additional_rules = []
        elif isinstance(additional_rules, dict):
            additional_rules = [additional_rules]

        def apply_rules(rule_set):
            for rule in rule_set:
                if not isinstance(rule, dict):
                    raise utils.FormatError("Adjust rule should be a dictionary.")
                condition = rule.get('when', True)
                continue_ = rule.get('continue', True)
                if not isinstance(continue_, bool):
                    raise utils.FormatError(
                        "The 'continue' value should be bool, got '{}' .".format(continue_))
                try:
                    if context.matches(condition):
                        if decision_callback:
                            decision_callback(node, rule, True)
                        apply_rule = {
                            item: value for item, value in rule.items()
                            if item not in ADJUST_CONTROL_KEYS
                            }
                        self.merger.merge(node.data, apply_rule, node.name)
                        if not continue_:
                            break
                    elif decision_callback:
                        decision_callback(node, rule, False)
                except fmf.context.CannotDecide:
                    if decision_callback:
                        decision_callback(node, rule, None)
                    if undecided == 'skip':
                        continue
                    if undecided == 'raise':
                        raise
                    raise utils.GeneralError(
                        "Invalid value for the 'undecided' parameter. Should be 'skip' or "
                        "'raise', got '{}' .".format(undecided))

        apply_rules(rules)
        if additional_rules_callback is None or additional_rules_callback(node):
            apply_rules(additional_rules)

        for child in node.children.values():
            self.adjust(child, context, key, undecided, case_sensitive,
                        decision_callback, additional_rules, additional_rules_callback)
