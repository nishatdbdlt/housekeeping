from odoo import fields, models


class RmgHkTemplate(models.Model):
    _name = 'rmg.hk.template'
    _description = 'Housekeeping Checklist'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    item_ids = fields.One2many('rmg.hk.template.item', 'template_id', string='Check Items')


class RmgHkTemplateItem(models.Model):
    _name = 'rmg.hk.template.item'
    _description = 'Housekeeping Checklist Item'
    _order = 'sequence, id'

    template_id = fields.Many2one('rmg.hk.template', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Check', required=True)
    critical = fields.Boolean(string='Critical', help='Safety / compliance critical item')
