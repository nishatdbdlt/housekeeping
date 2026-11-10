from odoo import fields, models


class RmgHkArea(models.Model):
    _name = 'rmg.hk.area'
    _description = 'Housekeeping Area'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    template_id = fields.Many2one('rmg.hk.template', string='Checklist', required=True)
    frequency = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly (Sat)'), ('monthly', 'Monthly (1st)'), ('manual', 'On demand')],
        default='daily', required=True)
    user_id = fields.Many2one('res.users', string='Responsible')
