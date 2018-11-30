# -*- coding: utf-8 -*-
"""The tgapp-resetpassword package"""


def plugme(app_config, options):
    try:  # TG2.3
        app_config['_pluggable_resetpassword_config'] = options
    except TypeError:  # TG2.4+
        app_config.update_blueprint({
            '_pluggable_resetpassword_config': options,
        })
    return dict(appid='resetpassword', global_helpers=False)

