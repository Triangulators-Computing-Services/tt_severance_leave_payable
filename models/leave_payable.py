# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class LeavePayable(models.Model):
    _name = 'leave.payable'

    name = fields.Char(string='Name')
    date_current = fields.Date(default=datetime.today())

    leave_payable_line_ids = fields.One2many('leave.payable.line', 'leave_payable_id')

    @api.multi
    def wage_calc(self):
        for record in self.leave_payable_line_ids:
            record.wage = record.contract_reference.wage

    @api.multi
    def populate_employees(self):
        if self.leave_payable_line_ids:
            for record in self.leave_payable_line_ids:
                record.unlink()

        emp = self.env['hr.employee'].search([])
        for record in emp:
            contract_find_return = self._contract_find(record)
            # Because the function returns two values, they are returned in the form of a tuple
            if contract_find_return:
                employee_data = {
                    "employee_name": record.id,
                    "contract_reference": contract_find_return[0],
                    "years_of_service": contract_find_return[1] / 365.25,
                    "leave_payable_id": self.id,
                }
                if contract_find_return[1] / 365.25 >= 0.5:
                    leave_obj = self.env["leave.payable.line"]
                    leave_obj.create(employee_data)

        self.wage_calc()

    @api.multi
    def _contract_find(self, employee=None):
        """Finds the contract of the employee in question"""
        domain = [('employee_id', '=', employee.id)]

        contract_result = self.env['hr.contract'].search(domain, limit=1)
        contract_id = fields.Many2one('hr.contract')

        difference = 0

        for record in contract_result:
            if record.provident_fund_applicable:
                return 0

            contract_date = datetime.strptime(record.date_start, "%Y-%m-%d")  # input contract starting date
            current_date = datetime.strptime(self.date_current, "%Y-%m-%d")  # input current date from Odoo
            timedelta = current_date - contract_date  # time difference between the dates
            diff = timedelta.days  # the time difference in days (out put is in 'Char')
            difference = int(diff)  # convert 'Char' into Int
            contract_id = record.id

        return contract_id, difference


class LeavePayableLine(models.Model):
    _name = 'leave.payable.line'

    leave_payable_id = fields.Many2one('leave.payable')

    employee_name = fields.Many2one('hr.employee', sting='Employee Name', readonly=True)
    contract_reference = fields.Many2one('hr.contract', string='Contract Reference', readonly=True)
    leave_remaining = fields.Integer(string='Remaining Leave')
    wage = fields.Float(strring='Wage')
    years_of_service = fields.Float(string='Years of Service')
