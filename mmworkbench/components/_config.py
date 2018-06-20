# -*- coding: utf-8 -*-
"""
This module contains the Config class.
"""
from __future__ import absolute_import, unicode_literals

import copy
import logging
import os
import warnings

from .. import path

logger = logging.getLogger(__name__)

CONFIG_DEPRECATION_MAPPING = {
    'DOMAIN_CLASSIFIER_CONFIG': 'DOMAIN_MODEL_CONFIG',
    'INTENT_CLASSIFIER_CONFIG': 'INTENT_MODEL_CONFIG',
    'ENTITY_RECOGNIZER_CONFIG': 'ENTITY_MODEL_CONFIG',
    'ROLE_CLASSIFIER_CONFIG': 'ROLE_MODEL_CONFIG',
    'ENTITY_RESOLVER_CONFIG': 'ENTITY_RESOLUTION_CONFIG',
    'get_entity_recognizer_config': 'get_entity_model_config',
    'get_intent_classifier_config': 'get_intent_model_config',
    'get_entity_resolver_config': 'get_entity_resolution_model_config',
    'get_role_classifier_config': 'get_role_model_config'
}

DEFAULT_DOMAIN_CLASSIFIER_CONFIG = {
    'model_type': 'text',
    'model_settings': {
        'classifier_type': 'logreg',
    },
    'param_selection': {
        'type': 'k-fold',
        'k': 10,
        'grid': {
            'fit_intercept': [True, False],
            'C': [10, 100, 1000, 10000, 100000]
        },
    },
    'features': {
        'bag-of-words': {
            'lengths': [1]
        },
        'freq': {'bins': 5},
        'in-gaz': {}
    }
}

DEFAULT_INTENT_CLASSIFIER_CONFIG = {
    'model_type': 'text',
    'model_settings': {
        'classifier_type': 'logreg'
    },
    'param_selection': {
        'type': 'k-fold',
        'k': 10,
        'grid': {
            'fit_intercept': [True, False],
            'C': [0.01, 1, 100, 10000, 1000000],
            'class_bias': [1, 0.7, 0.3, 0]
        }
    },
    'features': {
        'bag-of-words': {
            'lengths': [1]
        },
        'in-gaz': {},
        'freq': {'bins': 5},
        'length': {}
    }
}

DEFAULT_ENTITY_RECOGNIZER_CONFIG = {
    'model_type': 'tagger',
    'label_type': 'entities',
    'model_settings': {
        'classifier_type': 'memm',
        'tag_scheme': 'IOB',
        'feature_scaler': 'max-abs'
    },
    'param_selection': {
        'type': 'k-fold',
        'k': 5,
        'scoring': 'accuracy',
        'grid': {
            'penalty': ['l1', 'l2'],
            'C': [0.01, 1, 100, 10000, 1000000, 100000000]
        },
    },
    'features': {
        'bag-of-words-seq': {
            'ngram_lengths_to_start_positions': {
                1: [-2, -1, 0, 1, 2],
                2: [-2, -1, 0, 1]
            }
        },
        'in-gaz-span-seq': {},
        'sys-candidates-seq': {
            'start_positions': [-1, 0, 1]
        }
    }
}

DEFAULT_ENTITY_RESOLVER_CONFIG = {
    'model_type': 'text_relevance'
}

DOC_TYPE = 'document'

# ElasticSearch mapping to define text analysis settings for text fields.
# It defines specific index configuration for synonym indices. The common index configuration
# is in default index template.
DEFAULT_ES_SYNONYM_MAPPING = {
    "mappings": {
        DOC_TYPE: {
            "properties": {
                "sort_factor": {
                    "type": "double"
                },
                "whitelist": {
                    "type": "nested",
                    "properties": {
                        "name": {
                            "type": "text",
                            "fields": {
                                "raw": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                },
                                "normalized_keyword": {
                                    "type": "text",
                                    "analyzer": "keyword_match_analyzer"
                                },
                                "char_ngram": {
                                    "type": "text",
                                    "analyzer": "char_ngram_analyzer"
                                }
                            },
                            "analyzer": "default_analyzer"
                        }
                    }
                }
            }
        }
    }
}

DEFAULT_ROLE_CLASSIFIER_CONFIG = {
    'model_type': 'text',
    'model_settings': {
        'classifier_type': 'logreg'
    },
    'params': {
        'C': 100,
        'penalty': 'l1'
    },
    'features': {
        'bag-of-words-before': {
            'ngram_lengths_to_start_positions': {
                1: [-2, -1],
                2: [-2, -1]
            }
        },
        'bag-of-words-after': {
            'ngram_lengths_to_start_positions': {
                1: [0, 1],
                2: [0, 1]
            }
        },
        'other-entities': {}
    }
}

DEFAULT_ES_INDEX_TEMPLATE_NAME = "default"

# Default ES index template that contains the base index configuration shared across different
# types of indices. Currently all ES indices will be created using this template.
# - custom text analysis settings such as custom analyzers, token filters and character filters.
# - dynamic field mapping template for text fields
# - common fields, e.g. id.
DEFAULT_ES_INDEX_TEMPLATE = {
    "template": "*",
    "mappings": {
        DOC_TYPE: {
            "dynamic_templates": [
                {
                    "default_text": {
                        "match": "*",
                        "match_mapping_type": "string",
                        "mapping": {
                            "type": "text",
                            "analyzer": "default_analyzer",
                            "fields": {
                                "raw": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                },
                                "normalized_keyword": {
                                    "type": "text",
                                    "analyzer": "keyword_match_analyzer"
                                },
                                "char_ngram": {
                                    "type": "text",
                                    "analyzer": "char_ngram_analyzer"
                                }
                            }
                        }
                    }
                }
            ],
            "properties": {
                "id": {
                    "type": "keyword"
                }
            }
        }
    },
    "settings": {
        "analysis": {
            "char_filter": {
                "remove_loose_apostrophes": {
                    "pattern": " '|' ",
                    "type": "pattern_replace",
                    "replacement": ""
                },
                "space_possessive_apostrophes": {
                    "pattern": "([^\\p{N}\\s]+)'s ",
                    "type": "pattern_replace",
                    "replacement": "$1 's "
                },
                "remove_special_beginning": {
                    "pattern": "^[^\\p{L}\\p{N}\\p{Sc}&']+",
                    "type": "pattern_replace",
                    "replacement": ""
                },
                "remove_special_end": {
                    "pattern": "[^\\p{L}\\p{N}&']+$",
                    "type": "pattern_replace",
                    "replacement": ""
                },
                "remove_special1": {
                    "pattern": "([\\p{L}]+)[^\\p{L}\\p{N}&']+(?=[\\p{N}\\s]+)",
                    "type": "pattern_replace",
                    "replacement": "$1 "
                },
                "remove_special2": {
                    "pattern": "([\\p{N}]+)[^\\p{L}\\p{N}&']+(?=[\\p{L}\\s]+)",
                    "type": "pattern_replace",
                    "replacement": "$1 "
                },
                "remove_special3": {
                    "pattern": "([\\p{L}]+)[^\\p{L}\\p{N}&']+(?=[\\p{L}]+)",
                    "type": "pattern_replace",
                    "replacement": "$1 "
                },
                "remove_comma": {
                    "pattern": ",",
                    "type": "pattern_replace",
                    "replacement": ""
                },
                "remove_tm_and_r": {
                    "pattern": "™|®",
                    "type": "pattern_replace",
                    "replacement": ""
                }
            },
            "filter": {
                "token_shingle": {
                    "max_shingle_size": "4",
                    "min_shingle_size": "2",
                    "output_unigrams": "true",
                    "type": "shingle"
                },
                "ngram_filter": {
                    "type": "ngram",
                    "min_gram": "3",
                    "max_gram": "3"
                }
            },
            "analyzer": {
                "default_analyzer": {
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "token_shingle"
                    ],
                    "char_filter": [
                        "remove_comma",
                        "remove_tm_and_r",
                        "remove_loose_apostrophes",
                        "space_possessive_apostrophes",
                        "remove_special_beginning",
                        "remove_special_end",
                        "remove_special1",
                        "remove_special2",
                        "remove_special3"
                    ],
                    "type": "custom",
                    "tokenizer": "whitespace"
                },
                "keyword_match_analyzer": {
                    "filter": [
                        "lowercase",
                        "asciifolding"
                    ],
                    "char_filter": [
                        "remove_comma",
                        "remove_tm_and_r",
                        "remove_loose_apostrophes",
                        "space_possessive_apostrophes",
                        "remove_special_beginning",
                        "remove_special_end",
                        "remove_special1",
                        "remove_special2",
                        "remove_special3"
                    ],
                    "type": "custom",
                    "tokenizer": "keyword"
                },
                "char_ngram_analyzer": {
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "ngram_filter"
                    ],
                    "char_filter": [
                        "remove_comma",
                        "remove_tm_and_r",
                        "remove_loose_apostrophes",
                        "space_possessive_apostrophes",
                        "remove_special_beginning",
                        "remove_special_end",
                        "remove_special1",
                        "remove_special2",
                        "remove_special3"
                    ],
                    "type": "custom",
                    "tokenizer": "whitespace"
                }
            }
        }
    }
}


# Elasticsearch mapping to define knowledge base index specific configuration:
# - dynamic field mapping to index all synonym whitelist in fields with "$whitelist" suffix.
# - location field
#
# The common configuration is defined in default index template
DEFAULT_ES_QA_MAPPING = {
    "mappings": {
        DOC_TYPE: {
            "dynamic_templates": [
                {
                    "synonym_whitelist_text": {
                        "match": "*$whitelist",
                        "match_mapping_type": "object",
                        "mapping": {
                            "type": "nested",
                            "properties": {
                                "name": {
                                    "type": "text",
                                    "fields": {
                                        "raw": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        },
                                        "normalized_keyword": {
                                            "type": "text",
                                            "analyzer": "keyword_match_analyzer"
                                        },
                                        "char_ngram": {
                                            "type": "text",
                                            "analyzer": "char_ngram_analyzer"
                                        }
                                    },
                                    "analyzer": "default_analyzer"
                                }
                            }
                        }
                    }
                }
            ],
            "properties": {
                "location": {
                    "type": "geo_point"
                }
            }
        }
    }
}

DEFAULT_PARSER_DEPENDENT_CONFIG = {
    'left': True,
    'right': True,
    'min_instances': 0,
    'max_instances': None,
    'precedence': 'left',
    'linking_words': frozenset()
}

DEFAULT_RANKING_CONFIG = {
    'query_clauses_operator': 'or'
}

DEFAULT_NLP_CONFIG = {
    'extract_nbest_entities': []
}


def get_app_namespace(app_path):
    """Returns the namespace of the application at app_path"""
    try:
        _app_namespace = _get_config_module(app_path).APP_NAMESPACE
        if 'JUPYTER_USER' in os.environ:
            _app_namespace = '{}_{}'.format(os.environ['JUPYTER_USER'], _app_namespace)
        return _app_namespace
    except (OSError, IOError):
        logger.debug('No app configuration file found')
    except AttributeError:
        logger.debug('App namespace not set in app configuration')

    _app_namespace = os.path.split(app_path)[1]
    if 'JUPYTER_USER' in os.environ:
        _app_namespace = '{jupyter_user}_{app_namespace}'.format(
            jupyter_user=os.environ['JUPYTER_USER'], app_namespace=_app_namespace)
    return _app_namespace


def get_classifier_config(clf_type, app_path=None, domain=None, intent=None, entity=None):
    """Returns the config for the specified classifier, with the
    following  order of precedence.

    If the application contains a config.py file:
    - Return the response from the get_*_model_config function in
      config.py for the specified classifier type. E.g.
      `get_intent_model_config`.
    - If the function does not exist, or raise an exception, return the
      config specified by *_MODEL_CONFIG in config.py, e.g.
      INTENT_MODEL_CONFIG.

    Otherwise, use the workbench default config for the classifier type


    Args:
        clf_type (str): The type of the classifier. One of 'domain',
            'intent', 'entity', 'entity_resolution', or 'role'.
        app_path (str, optional): The location of the app
        domain (str, optional): The domain of the classifier
        intent (str, optional): The intent of the classifier
        entity (str, optional): The entity type of the classifier

    Returns:
        dict: A classifier config
    """
    try:
        module_conf = _get_config_module(app_path)

    except (OSError, IOError):
        logger.info('No app configuration file found. Using default %s model configuration',
                    clf_type)
        return _get_default_classifier_config(clf_type)

    func_name = {
        'intent': 'get_intent_classifier_config',
        'entity': 'get_entity_recognizer_config',
        'entity_resolution': 'get_entity_resolver_config',
        'role': 'get_role_classifier_config',
    }.get(clf_type)
    func_args = {
        'intent': ('domain',),
        'entity': ('domain', 'intent'),
        'entity_resolution': ('domain', 'intent', 'entity'),
        'role': ('domain', 'intent', 'entity'),
    }.get(clf_type)

    if func_name:
        func = None
        try:
            func = getattr(module_conf, func_name)
        except AttributeError:
            try:
                func = getattr(module_conf, CONFIG_DEPRECATION_MAPPING[func_name])
                msg = '%s config key is deprecated. Please use the equivalent %s config ' \
                      'key' % (CONFIG_DEPRECATION_MAPPING[func_name], func_name)
                warnings.warn(msg, DeprecationWarning)
            except AttributeError:
                pass
        if func:
            try:
                raw_args = {'domain': domain, 'intent': intent, 'entity': entity}
                args = {k: raw_args[k] for k in func_args}
                return copy.deepcopy(func(**args))
            except Exception as exc:
                # Note: this is intentionally broad -- provider could raise any exception
                logger.warning('%r configuration provider raised exception: %s', clf_type, exc)

    attr_name = {
        'domain': 'DOMAIN_CLASSIFIER_CONFIG',
        'intent': 'INTENT_CLASSIFIER_CONFIG',
        'entity': 'ENTITY_RECOGNIZER_CONFIG',
        'entity_resolution': 'ENTITY_RESOLVER_CONFIG',
        'role': 'ROLE_CLASSIFIER_CONFIG',
    }[clf_type]
    try:
        return copy.deepcopy(getattr(module_conf, attr_name))
    except AttributeError:
        try:
            result = copy.deepcopy(getattr(module_conf, CONFIG_DEPRECATION_MAPPING[attr_name]))
            msg = '%s config is deprecated. Please use the equivalent %s config ' \
                  'key' % (CONFIG_DEPRECATION_MAPPING[attr_name], attr_name)
            warnings.warn(msg, DeprecationWarning)
            return result
        except AttributeError:
            logger.info('No %s model configuration set. Using default.', clf_type)

    return _get_default_classifier_config(clf_type)


def _get_default_classifier_config(clf_type):
    return copy.deepcopy({
        'domain': DEFAULT_DOMAIN_CLASSIFIER_CONFIG,
        'intent': DEFAULT_INTENT_CLASSIFIER_CONFIG,
        'entity': DEFAULT_ENTITY_RECOGNIZER_CONFIG,
        'entity_resolution': DEFAULT_ENTITY_RESOLVER_CONFIG,
        'role': DEFAULT_ROLE_CLASSIFIER_CONFIG
    }[clf_type])


def get_parser_config(app_path=None, config=None, domain=None, intent=None):
    """Gets the fully specified parser configuration for the app at the
    given path.

    Args:
        app_path (str, optional): The location of the workbench app
        config (dict, optional): A config object to use. This will
            override the config specified by the app's config.py file.
            If necessary, this object will be expanded to a fully
            specified config object.
        domain (str, optional): The domain of the parser
        intent (str, optional): The intent of the parser

    Returns:
        dict: A fully parser configuration
    """
    if config:
        return _expand_parser_config(config)
    try:
        module_conf = _get_config_module(app_path)
    except (OSError, IOError):
        logger.info('No app configuration file found. Not configuring parser.')
        return _get_default_parser_config()

    # Try provider first
    config_provider = None
    try:
        config_provider = module_conf.get_parser_config
    except AttributeError:
        pass
    if config_provider:
        try:
            config = config or config_provider(domain, intent)
            return _expand_parser_config(config)
        except Exception as exc:
            # Note: this is intentionally broad -- provider could raise any exception
            logger.warning('Parser configuration provider raised exception: %s', exc)

    # Try object second
    try:
        config = config or module_conf.PARSER_CONFIG
        return _expand_parser_config(config)
    except AttributeError:
        pass

    return _get_default_parser_config()


def _get_default_parser_config():
    return None


def _expand_parser_config(config):
    return {head: _expand_group_config(group) for head, group in config.items()}


def _expand_group_config(group_config):
    """Expands a parser group configuration.

    A group config can either be a list of dependents or a dictionary with a
    field for each dependent.

    In the list a dependent can be a string containing the name of the
    entity-role type identifier or a dictionary with at least a type field.

    In the dictionary the dependent must be another dictionary.

    Some example parser configs follow below.

    A very simple configuration:

       {
           'head': ['dependent']
       }

    A more realistic simple config:

        {
            'product|beverage': ['size', 'quantity', 'option|beverage'],
            'product|baked-good': ['size', 'quantity', 'option|baked-good'],
            'store': ['location'],
            'option': ['size']
        }

    A fully specified config:

        {
            'product': {
                'quantity': {
                    'left': True,
                    'right': True,
                    'precedence': 'left',
                    'min_instances': 0,
                    'max_instances': 3
                },
                'size': {
                    'left': True,
                    'right': True,
                    'precedence': 'left',
                    'min_instances': 0,
                    'max_instances': 1
                },
                'option': {
                    'left': True,
                    'right': True,
                    'precedence': 'left',
                    'min_instances': 0,
                    'max_instances': 1
                }
            },
            'store': {
                'location': {
                    'left': True,
                    'right': True,
                    'precedence': 'left',
                    'min_instances': 0,
                    'max_instances': 1
                }
            },
            'option': {
                'size': {
                    'left': True,
                    'right': True,
                    'precedence': 'left',
                    'min_instances': 0,
                    'max_instances': 1
                }
            }
        }
    """
    group_config = copy.deepcopy(group_config)
    expanded = {}
    if isinstance(group_config, (tuple, list, set)):
        for dependent in group_config:
            config = copy.copy(DEFAULT_PARSER_DEPENDENT_CONFIG)
            try:
                dep_type = dependent.pop('type')
                config.update(dependent)
            except (AttributeError, ValueError):
                # simple style config -- dependent is a str
                dep_type = dependent

            expanded[dep_type] = config
    else:
        for dep_type, dep_config in group_config.items():
            config = copy.copy(DEFAULT_PARSER_DEPENDENT_CONFIG)
            dep_config.pop('type', None)
            config.update(dep_config)
            expanded[dep_type] = config
    return expanded


def _get_config_module(app_path):
    module_path = path.get_config_module_path(app_path)

    import imp
    config_module = imp.load_source('config_module', module_path)
    return config_module


def _get_default_nlp_config():
    return copy.deepcopy(DEFAULT_NLP_CONFIG)


def get_nlp_config(app_path=None, config=None):
    """Gets the fully specified processor configuration for the app at the
    given path.

    Args:
        app_path (str, optional): The location of the workbench app
        config (dict, optional): A config object to use. This will
            override the config specified by the app's config.py file.
            If necessary, this object will be expanded to a fully
            specified config object.

    Returns:
        dict: The nbest inference configuration
    """
    if config:
        return config
    try:
        module_conf = _get_config_module(app_path)
    except (OSError, IOError):
        logger.info('No app configuration file found. Not configuring nbest inference.')
        return _get_default_nlp_config()

    # Try provider first
    try:
        return copy.deepcopy(module_conf.get_nlp_config())
    except AttributeError:
        pass

    # Try object second
    try:
        config = config or module_conf.NLP_CONFIG
        return config
    except AttributeError:
        pass

    return _get_default_nlp_config()
