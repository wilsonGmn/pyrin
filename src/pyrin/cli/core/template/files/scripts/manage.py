# -*- coding: utf-8 -*-
"""
manage module.

to enable locale management for application, execute:
`python manage.py babel enable`

to enable migrations for application, execute:
`python manage.py alembic enable`
"""

import fire

from pyrin.database.migration.alembic.cli import AlembicCLI
from pyrin.globalization.locale.babel.cli import BabelCLI

from APPLICATION_PACKAGE import APPLICATION_CLASS


app_instance = APPLICATION_CLASS(scripting_mode=True)


class Groups(object):
    """
    groups class.

    each cli handler group is resided in its relevant group name.

    usage example:

    `python manage.py alembic upgrade --arg value`
    `python manage.py babel extract --arg value`
    """

    def __init__(self):
        """
        initializes an instance of Groups.
        """

        self.babel = BabelCLI()
        self.alembic = AlembicCLI()


if __name__ == '__main__':
    fire.Fire(Groups())
