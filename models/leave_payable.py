# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class LeavePayable(models.Model):
    _name = 'leave.payable'

    name = fields.Char(string='Name', readonly=True)
    date_current = fields.Date(default=datetime.today())

    config_reference = fields.Many2one('severance.config.general', string='Config Reference')
    turnover_rate = fields.Float(string="Turnover Rate (%)", required=True, default=100.00)
    total_annual_leave_payable = fields.Float(string='Total Annual Leave Payable', readonly=True)

    leave_payable_line_ids = fields.One2many('leave.payable.line', 'leave_payable_id')

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("awaiting_approval", "Awaiting Approval"),
            ("cancelled", "Cancelled"),
            ("approved", "Approved"),
        ], default="draft", string="Status", track_visibility='onchange',
    )

    @api.multi
    def calculate_payable(self):
        gross_annual_leave_payable = 0.00
        for record in self.leave_payable_line_ids:
            record.wage = record.contract_reference.wage
            wage_per_day = record.wage / self.config_reference.working_days
            record.annual_leave_payable = wage_per_day * record.leaves
            gross_annual_leave_payable += record.annual_leave_payable

        self.total_annual_leave_payable = (gross_annual_leave_payable * self.turnover_rate) /100

        self.state = "awaiting_approval"

    @api.multi
    def populate_employees(self):
        """Fetches employees with their contracts and continues to execute calculate_payable()"""
        employee_ids = self.env['hr.employee'].search([])

        for record in employee_ids:
            domain = [('employee_id', '=', record.id)]
            contract_result = self.env['hr.contract'].search(domain, limit=1)  # contract search for employee

            emp_data = {
                "employee_name": record.id,
                "contract_reference": contract_result.id,
                "leaves": record.remaining_leaves,
                "leave_payable_id": self.id,
            }
            emp_line_obj = self.env['leave.payable.line']
            emp_line_obj.create(emp_data)

        self.calculate_payable()

    @api.multi
    def cancel(self):
        self.state = "cancelled"

    @api.multi
    def revert(self):
        self.state = "awaiting_approval"

    @api.multi
    def approve(self):
        annual_leave_data = {
            "total_annual_leave_payable": self.total_severance_forecast,
            "leave_payable_reference": self.id,
        }
        self.env['leave.payable'].create(annual_leave_data)  # records the computed data to readonly model

        self.state = "approved"

    @api.model
    def create(self, vals):
        vals["name"] = "Annual Leave Payable of " + str(datetime.now().year)
        return super(LeavePayable, self).create(vals)

    @api.model
    def unlink(self):  # TODO fix delete issue
        for record in self:
            if record.state not in ("draft", "awaiting_approval", "cancelled"):
                raise Warning(_("You cannot delete a record that has been approved."))
        return super(LeavePayable, self).unlink()


class LeavePayableLine(models.Model):
    _name = 'leave.payable.line'

    leave_payable_id = fields.Many2one('leave.payable')

    employee_name = fields.Many2one('hr.employee', sting='Employee Name', readonly=True)
    contract_reference = fields.Many2one('hr.contract', string='Contract Reference', readonly=True)
    leaves = fields.Integer(string='Remaining Leave')
    wage = fields.Float(strring='Wage')
    years_of_service = fields.Float(string='Years of Service')
    annual_leave_payable = fields.Float(string="Annual Leave Payable")
