"""KoomBook conf"""
from .kb import *  # noqa

LANGUAGE_CODE = 'fr'
IDEASCUBE_NAME = 'Institut Français Burundi'
HOME_CARDS = HOME_CARDS + [  # pragma: no flakes
    {
        'id': 'appinventor',
    },
]
