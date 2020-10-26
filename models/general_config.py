# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class SeveranceEligible(models.Model):
    _name = 'severance.config.general'
    _inherit = 'res.config.settings'
    _description = "General configurations for severance and Annual Leave Payable calculations"

    name = fields.Char(string='Name')

    # turn_over_estimation = fields.Float(string='Turn Over Estimation (%)', required=True)
    # severance_period = fields.Integer(string='Severance Payable Period (months)', required=True)
    severance_eligibility_period = fields.Integer(string='Severance Eligibility Period (Years)', required=True)
    working_days = fields.Integer(string='Number of Working Days in a Month', required=True)
    retirement_age = fields.Integer(string='Retirement Age')

    tax_ids = fields.One2many('config.tax.conditions', 'general_config_reference')

    # leave_line_ids = fields.One2many('config.leave.line', 'general_config_reference')


class ConfigTaxConditions(models.Model):
    _name = 'config.tax.conditions'

    general_config_reference = fields.Many2one('severance.config.general')

    range_one = fields.Float(string='Range One')
    range_two = fields.Float(string='Range Two')
    tax_rate = fields.Float(string='Tax Rate (%)')
    exemption = fields.Float(string='Exemption')


# class ConfigLeaveLine(models.Model):
#     _name = 'config.leave.line'
#
#     general_config_reference = fields.Many2one('severance.config.general')
#
#     leave_type = fields.Many2one('hr.holidays.status', string='Leave Type', required=True)