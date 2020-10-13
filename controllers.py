# -*- coding: utf-8 -*-
from openerp import http

# class TtSeveranceLeavePayable(http.Controller):
#     @http.route('/tt_severance_leave_payable/tt_severance_leave_payable/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tt_severance_leave_payable/tt_severance_leave_payable/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tt_severance_leave_payable.listing', {
#             'root': '/tt_severance_leave_payable/tt_severance_leave_payable',
#             'objects': http.request.env['tt_severance_leave_payable.tt_severance_leave_payable'].search([]),
#         })

#     @http.route('/tt_severance_leave_payable/tt_severance_leave_payable/objects/<model("tt_severance_leave_payable.tt_severance_leave_payable"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tt_severance_leave_payable.object', {
#             'object': obj
#         })