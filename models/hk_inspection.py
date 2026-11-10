from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class RmgHkInspection(models.Model):
    _name = 'rmg.hk.inspection'
    _description = 'Housekeeping Inspection'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    date = fields.Date(default=fields.Date.context_today, required=True)
    area_id = fields.Many2one('rmg.hk.area', string='Area', required=True)
    template_id = fields.Many2one('rmg.hk.template', string='Checklist')
    user_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user)
    state = fields.Selection([('draft', 'To Do'), ('done', 'Done')], default='draft', tracking=True)
    line_ids = fields.One2many('rmg.hk.inspection.line', 'inspection_id', string='Checklist')
    note = fields.Text(string='Remarks')
    ok_count = fields.Integer(compute='_compute_stats', store=True)
    issue_count = fields.Integer(string='Issues', compute='_compute_stats', store=True)
    score = fields.Float(string='Score %', compute='_compute_stats', store=True, aggregator='avg')

    @api.depends('line_ids.result')
    def _compute_stats(self):
        for rec in self:
            ok = len(rec.line_ids.filtered(lambda l: l.result == 'ok'))
            no = len(rec.line_ids.filtered(lambda l: l.result == 'no'))
            rec.ok_count = ok
            rec.issue_count = no
            rec.score = (ok * 100.0 / (ok + no)) if (ok + no) else 0.0

    @api.model
    def _template_cmds(self, template):
        return [Command.create({'name': i.name, 'critical': i.critical, 'sequence': i.sequence})
                for i in template.item_ids]

    @api.onchange('area_id')
    def _onchange_area_id(self):
        tmpl = self.area_id.template_id
        self.template_id = tmpl
        self.line_ids = [Command.clear()] + (self._template_cmds(tmpl) if tmpl else [])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('rmg.hk.inspection') or 'New'
            if vals.get('area_id') and not vals.get('template_id'):
                vals['template_id'] = self.env['rmg.hk.area'].browse(vals['area_id']).template_id.id
        records = super().create(vals_list)
        for rec in records:
            if rec.template_id and not rec.line_ids:
                rec.line_ids = self._template_cmds(rec.template_id)
        return records

    def action_all_ok(self):
        self.line_ids.filtered(lambda l: not l.result).write({'result': 'ok'})

    def action_done(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            if any(not l.result for l in rec.line_ids):
                raise UserError(_("Some items are not checked. Tap 'All OK' first, then mark only the problems."))
            for line in rec.line_ids.filtered(lambda l: l.result == 'no'):
                self.env['rmg.hk.issue'].create({
                    'name': line.name,
                    'note': line.remark,
                    'area_id': rec.area_id.id,
                    'inspection_id': rec.id,
                    'critical': line.critical,
                    'user_id': rec.area_id.user_id.id or False,
                })
            rec.state = 'done'

    @api.model
    def _cron_generate_inspections(self):
        today = fields.Date.context_today(self)
        fallback = self.env.ref('base.user_admin')
        areas = self.env['rmg.hk.area'].search([('frequency', '!=', 'manual'), ('template_id', '!=', False)])
        for area in areas:
            if area.frequency == 'weekly' and today.weekday() != 5:
                continue
            if area.frequency == 'monthly' and today.day != 1:
                continue
            if self.search_count([('area_id', '=', area.id), ('date', '=', today)]):
                continue
            self.create({'area_id': area.id, 'date': today, 'user_id': (area.user_id or fallback).id})


class RmgHkInspectionLine(models.Model):
    _name = 'rmg.hk.inspection.line'
    _description = 'Housekeeping Inspection Line'
    _order = 'sequence, id'

    inspection_id = fields.Many2one('rmg.hk.inspection', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Check', required=True)
    critical = fields.Boolean(string='Critical')
    result = fields.Selection([('ok', 'OK'), ('no', 'Not OK'), ('na', 'N/A')])
    remark = fields.Char()
    state = fields.Selection(related='inspection_id.state')

    def action_ok(self):
        self.write({'result': 'ok'})

    def action_no(self):
        self.write({'result': 'no'})

    def action_na(self):
        self.write({'result': 'na'})
