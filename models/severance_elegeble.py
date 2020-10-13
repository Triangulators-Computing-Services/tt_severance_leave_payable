# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp import exceptions
from datetime import datetime


class SeveranceEligible(models.Model):
    _name = 'severance.eligible'
    _description = "finds and stores all eligible employees for severance pay"

    name = fields.Char(string='Name')
    current_date = fields.Date(default=datetime.today())
    config_reference = fields.Many2one('severance.config.general', string='General Configuration', required=True)
    turn_over_rate = fields.Float(string='Turnover Rate (%)')

    total_severance_forecast = fields.Float(string='Total Severance Amount ', readonly=True)
    tax_amount = fields.Float(string='Tax Amount')
    net_severance_value = fields.Float(string='Net Severance Value')
    past_year_severance = fields.Float(string='Past year severance')

    severance_eligible_lines = fields.One2many('severance.eligible.line', 'severance_eligible_id')

    @api.multi
    def calculate_severance(self):
        total_net_severance = 0.00
        total_severance_after_tax = 0.00
        total_severance_tax = 0.00
        for record in self.severance_eligible_lines:
            record.wage = record.contract_reference.wage
            record.severance_pay_per_month = (record.years_of_service - (record.years_of_service - 1)) + ((record.years_of_service - 1) / 3)
            record.severance_payable = record.wage * record.severance_pay_per_month
            # record.severance_tax_payable = record.severance_payable * 0.15

            # for tax_config in self.config_reference.tax_ids:
            #     if tax_config.range_two:
            #         if tax_config.range_one < record.wage <= tax_config.range_two:
            #             record.severance_tax_payable = ((record.wage * (tax_config.tax_rate / 100)) - tax_config.exemption) * record.severance_pay_per_month
            #     else:
            #         record.severance_tax_payable = ((record.wage * (tax_config.tax_rate / 100)) - tax_config.exemption) * record.severance_pay_per_month

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

            total_severance_tax += record.severance_tax_payable
            total_net_severance += record.wage
            # total_severance_after_tax += record.severance_payable_after_tax

        # total_severance = total_net_severance * self.config_reference.severance_period
        self.total_severance_forecast = total_net_severance * self.turn_over_rate / 100
        self.tax_amount = total_severance_tax * self.turn_over_rate / 100

    @api.multi
    def populate_employees(self):
        if self.severance_eligible_lines:
            for record in self.severance_eligible_lines:
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
                    "severance_eligible_id": self.id,
                }
                if contract_find_return[1] / 365.25 >= self.config_reference.severance_eligibility_period:
                    # for rec in contract_find_return[0].struct_id.rule_ids:
                    #     if rec is
                    severance_eligible = self.env["severance.eligible.line"]
                    severance_eligible.create(employee_data)

        self.calculate_severance()

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
            current_date = datetime.strptime(self.current_date, "%Y-%m-%d")  # input current date from Odoo
            timedelta = current_date - contract_date  # time difference between the dates
            diff = timedelta.days  # the time difference in days (out put is in 'Char')
            difference = int(diff)  # convert 'Char' into Int
            contract_id = record.id

        return contract_id, difference

    # @api.model
    # def create(self, vals):
    #     vals["name"] = self.env["ir.sequence"].next_by_code("salary_increment.record.seq")
    #     return super(EfficiencyInput, self).create(vals)
    #
    # @api.model
    # def unlink(self):
    #     for record in self:
    #         if record.state not in ("draft", "awaiting_approval"):
    #             raise Warning(_("You cannot delete a record that has been approved."))
    #     return super(EfficiencyInput, self).unlink()


class SeveranceEligibleLine(models.Model):
    _name = 'severance.eligible.line'

    severance_eligible_id = fields.Many2one('severance.eligible')

    employee_name = fields.Many2one('hr.employee', sting='Employee Name', readonly=True)
    contract_reference = fields.Many2one('hr.contract', string='Contract Reference', readonly=True)
    years_of_service = fields.Integer(string='Years of Service')
    wage = fields.Float(string='Wage')
    total_wage = fields.Float(string='Total Wage')
    diff = fields.Integer(string='Years of Service')
    severance_payable = fields.Float(string='Severance Payable')
    severance_tax_payable = fields.Float(string='Severance Tax')
    severance_payable_after_tax = fields.Float(string='Net Severance Payable')
    severance_pay_per_month = fields.Float(string='Severance Pay Per month')
    income_tax = fields.Float(string='Income Tax')
