"""KoomBook conf"""
from .kb import *  # pragma: no flakes

LANGUAGE_CODE = 'fr'
IDEASCUBE_NAME = 'Coeur de Forêt'
HOME_CARDS = STAFF_HOME_CARDS + [  # pragma: no flakes
    {
        'id': 'blog',
    },
    {
        'id': 'mediacenter',
    },
    {
        'id': 'appinventor',
    },
]
