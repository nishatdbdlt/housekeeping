from odoo import fields, models


class RmgHkIssue(models.Model):
    _name = 'rmg.hk.issue'
    _description = 'Housekeeping Issue'
    _inherit = ['mail.thread']
    _order = 'critical desc, date desc, id desc'

    name = fields.Char(string='Issue', required=True)
    area_id = fields.Many2one('rmg.hk.area', string='Area')
    inspection_id = fields.Many2one('rmg.hk.inspection', string='Inspection', ondelete='set null')
    critical = fields.Boolean(string='Critical')
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([('open', 'Open'), ('fixed', 'Fixed')], default='open', tracking=True)
    fixed_date = fields.Date(readonly=True)
    note = fields.Text(string='Remarks')

    def action_fix(self):
        self.write({'state': 'fixed', 'fixed_date': fields.Date.context_today(self)})
