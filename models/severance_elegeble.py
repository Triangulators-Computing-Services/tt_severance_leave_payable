# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class SeveranceEligible(models.Model):
    _name = 'severance.eligible'
    _description = "finds and stores all eligible employees for severance pay"

    name = fields.Char(string='Name', readonly=True, store=True, compute='set_fiscal_year_name')

    fiscal_year = fields.Many2one('account.fiscalyear', string='Fiscal Year', required=True)
    # fiscal_year_name = fields.Char(string="Fiscal Year Name", compute='set_fiscal_year_name')

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    config_reference = fields.Many2one('severance.config.general', required=True)
    turn_over_rate = fields.Float(string='Turnover Rate One (%)', required=True, default=100.00)
    turn_over_rate_q = fields.Float(string='Turnover Rate Two (%)', required=True, default=100.00)
    eligibility_period = fields.Integer(string="Eligibility Period", readonly=True, invisible=True)

    total_severance_forecast = fields.Float(string='Total Severance Amount ', readonly=True)  # before tax
    tax_amount = fields.Float(string='Total Tax Payable', readonly=True)  # total tax
    net_severance_value = fields.Float(string='Total Net Payable', readonly=True)  # after tax
    past_year_severance = fields.Float(string='Past year severance')

    severance_eligible_lines = fields.One2many('severance.eligible.line', 'severance_eligible_id')

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("awaiting_approval", "Awaiting Approval"),
            ("cancelled", "Cancelled"),
            ("approved", "Approved"),
        ], default="draft", string="Status", track_visibility='onchange',
    )

    @api.depends('fiscal_year')
    def set_fiscal_year_name(self):
        self.name = "Severance payable of " + self.fiscal_year.name

    @api.multi
    def calculate_severance(self):
        for record in self.severance_eligible_lines:
            record.wage = record.contract_reference.wage
            if record.years_of_service >= 12.00:
                record.severance_pay_per_month = 12.00
            else:
                record.severance_pay_per_month = 1 + ((record.years_of_service - 1) / 3)

            record.severance_payable = record.wage * record.severance_pay_per_month

            if record.wage > 10900:
                record.severance_tax_payable = record.wage * 0.35 - 1500
            elif 7800 < record.wage <= 10900:
                record.severance_tax_payable = record.wage * 0.30 - 955
            elif 5250 < record.wage <= 7800:
                record.severance_tax_payable = record.wage * 0.25 - 565
            elif 3200 < record.wage <= 5250:
                record.severance_tax_payable = record.wage * 0.20 - 302.50
            elif 1650 < record.wage <= 3200:
                record.severance_tax_payable = record.wage * 0.15 - 142.50
            elif 600 < record.wage <= 1650:
                record.severance_tax_payable = record.wage * 0.10 - 60

            record.severance_payable_after_tax = (record.wage * record.severance_pay_per_month) - record.severance_tax_payable

        self.calculate_total()

    @api.multi
    def calculate_total(self):
        """Calculates total_severance_forecast, net_severance_value and tax_amount with turnover rate"""
        over_eligible_total_severance = 0.00
        under_eligible_total_severance = 0.00
        over_eligible_total_tax = 0.00
        under_eligible_total_tax = 0.00
        over_eligible_total_net = 0.00
        under_eligible_total_net = 0.00
        for record in self.severance_eligible_lines:
            if record.contract_start_eval >= 5:
                over_eligible_total_severance += record.severance_payable
                over_eligible_total_tax += record.severance_tax_payable
                over_eligible_total_net += record.severance_payable_after_tax
            elif record.contract_start_eval < 5:
                under_eligible_total_severance += record.severance_payable
                under_eligible_total_tax += record.severance_tax_payable
                under_eligible_total_net += record.severance_payable_after_tax

        self.total_severance_forecast = (over_eligible_total_severance * self.turn_over_rate / 100) + (
                    under_eligible_total_severance * self.turn_over_rate_q / 100)
        self.net_severance_value = (over_eligible_total_net * self.turn_over_rate / 100) + (
                    under_eligible_total_net * self.turn_over_rate_q / 100)
        self.tax_amount = (over_eligible_total_tax * self.turn_over_rate / 100) + (
                    under_eligible_total_tax * self.turn_over_rate_q / 100)

    @api.multi
    def populate_employees(self):
        """Populates eligible employees and call the severance compute functions"""
        if self.severance_eligible_lines:
            for record in self.severance_eligible_lines:
                record.unlink()
        emp = self.env['hr.employee'].search([])
        for record in emp:
            contract_find_return = self._contract_find(record)
            # Because the function _contract_find(record) returns two values, they are returned in the form of a tuple
            if contract_find_return:
                employee_data = {
                    "employee_name": record.id,
                    "contract_reference": contract_find_return[0],
                    "years_of_service": contract_find_return[1] / 365.25,
                    "contract_start_eval": contract_find_return[2] / 365.25,
                    "severance_eligible_id": self.id,
                }
                if contract_find_return[1] / 365.25 >= self.config_reference.severance_eligibility_period and contract_find_return[3] <= self.config_reference.retirement_age:
                    severance_eligible = self.env["severance.eligible.line"]
                    severance_eligible.create(employee_data)

        self.calculate_severance()
        self.state = "awaiting_approval"

    @api.multi
    def _contract_find(self, employee=None):
        """
        Finds the contract of the employee in question and the years of service with regards to the start and end dates
        Also returns age of employee
        """
        domain = [('employee_id', '=', employee.id)]  # the id of the employee passed in the function parameter

        contract_result = self.env['hr.contract'].search(domain, limit=1)

        # values to be returned
        contract_id = fields.Many2one('hr.contract')
        difference = 0  # is years_of_service relative with end_date
        difference2 = 0  # is years_of_service relative with start_date
        age = 0

        for record in contract_result:
            if record.provident_fund_applicable:
                return 0

            # dates
            contract_date = datetime.strptime(record.date_start, "%Y-%m-%d")
            end_date = datetime.strptime(self.fiscal_year.date_stop, "%Y-%m-%d")
            start_date = datetime.strptime(self.fiscal_year.date_start, "%Y-%m-%d")

            timedelta = end_date - contract_date  # time difference between the dates
            timedelta2 = start_date - contract_date

            difference = float(timedelta.days)  # time difference between ending date and contract date
            difference2 = float(timedelta2.days)  # time difference between starting date and contract date
            contract_id = record.id

            if record.employee_id.birthday:  # computes the age of the given employee as long as it is entered
                birthday = datetime.strptime(record.employee_id.birthday, "%Y-%m-%d")
                timedelta_birthday = end_date - birthday
                age = int(timedelta_birthday.days) / 365.25
            # else:
            #     raise Warning("Please enter all the birthdays of employees for retirement calculation")

        return contract_id, difference, difference2, age

    @api.multi
    def cancel(self):
        self.state = "cancelled"

    @api.multi
    def revert(self):
        self.state = "awaiting_approval"

    @api.multi
    def approve(self):
        severance_data = {
            "name": self.name,
            "fiscal_year": self.fiscal_year,
            "total_severance": self.total_severance_forecast,
            "tax_amount": self.tax_amount,
            "net_severance_value": self.net_severance_value,
            # "severance_reference": self.id,
        }
        self.env['severance.records'].create(severance_data)  # records the computed data to readonly model

        self.eligibility_period = self.config_reference.severance_eligibility_period

        self.state = "approved"

    # @api.model
    # def create(self, vals):
    #     # vals["name"] = "Severance payable of " + vals["fiscal_year_name"]
    #     return super(SeveranceEligible, self).create(vals)

    @api.model
    def unlink(self):  # TODO fix delete issue
        for record in self:
            if record.state not in ("draft", "awaiting_approval", "cancelled"):
                raise Warning(_("You cannot delete a record that has been approved."))
        return super(SeveranceEligible, self).unlink()


class SeveranceEligibleLine(models.Model):
    _name = 'severance.eligible.line'

    severance_eligible_id = fields.Many2one('severance.eligible')

    employee_name = fields.Many2one('hr.employee', sting='Employee Name', readonly=True)
    contract_reference = fields.Many2one('hr.contract', string='Contract Reference', readonly=True)

    years_of_service = fields.Float(string='Years of Service', readonly=True)
    contract_start_eval = fields.Integer()

    wage = fields.Float(string='Wage')

    severance_payable = fields.Float(string='Severance Payable', readonly=True)
    severance_tax_payable = fields.Float(string='Severance Tax', readonly=True)
    severance_payable_after_tax = fields.Float(string='Net Payable', readonly=True)
    severance_pay_per_month = fields.Float(string='Severance Pay Per month')
