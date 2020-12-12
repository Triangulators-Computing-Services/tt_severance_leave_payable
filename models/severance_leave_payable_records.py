# -*- coding: utf-8 -*-

from openerp import models, fields, api


class SeveranceRecords(models.Model):
    _name = 'severance.records'
    _description = "Stores Severance Records"

    name = fields.Char(string='Name')
    fiscal_year = fields.Many2one('account.fiscalyear', string='Fiscal Year')
    total_severance = fields.Float(string='Total Severance Amount ', readonly=True)  # before tax
    tax_amount = fields.Float(string='Total Tax Payable', readonly=True)  # total tax
    net_severance_value = fields.Float(string='Total Net Payable', readonly=True)  # after tax

    severance_reference = fields.Many2one('severance.eligible')


class LeavePayableRecords(models.Model):
    _name = 'leave.payable.records'
    _description = "Stores Annual Leave Payable Records"

    name = fields.Char(string='Name')
    fiscal_year = fields.Many2one('account.fiscalyear', string='Fiscal Year')
    total_annual_leave_payable = fields.Float(string='Total Annual Leave Payable')

    leave_payable_reference = fields.Many2one('leave.payable')