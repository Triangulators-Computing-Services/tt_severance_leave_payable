# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class SeveranceEligible(models.Model):
    _inherit = 'hr.contract'

    provident_fund_applicable = fields.Boolean(string='Provident Fund Applicable')
