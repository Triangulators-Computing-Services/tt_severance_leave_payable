# -*- coding: utf-8 -*-
{
    'name': "tt_severance_leave_payable",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_contract'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'templates.xml',
        'views/severance_eligible_view.xml',
        'views/config_general_view.xml',
        'views/hr_contract.xml',
        'views/leave_payable_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}