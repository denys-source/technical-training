from odoo import models, fields, api, exceptions


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Properties"

    name = fields.Char(required=True)
    description = fields.Text()
    estate_property_type_id = fields.Many2one("estate.property.type")
    buyer_id = fields.Many2one("res.partner", copy=False)
    salesperson_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user
    )
    tag_ids = fields.Many2many("estate.property.tag")
    offer_ids = fields.One2many("estate.property.offer", "property_id")
    best_price = fields.Float(compute="_compute_best_price")
    postcode = fields.Char()
    date_availability = fields.Date(
        default=lambda _: fields.Datetime.add(fields.Date.today(), months=3),
        copy=False,
    )
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(
        readonly=True,
        copy=False,
    )
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    total_area = fields.Integer(compute="_compute_total_area")
    garden_orientation = fields.Selection(
        selection=[
            ("north", "North"),
            ("south", "South"),
            ("east", "East"),
            ("west", "West"),
        ]
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        selection=[
            ("new", "New"),
            ("offer_received", "Offer Received"),
            ("sold", "Sold"),
            ("canceled", "Canceled"),
        ],
        readonly=True,
        default="new",
    )

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for property in self:
            property.total_area = property.living_area + property.garden_area

    @api.depends("offer_ids")
    def _compute_best_price(self):
        for property in self:
            property.best_price = max(
                property.offer_ids.mapped("price"), default=0
            )

    @api.onchange("garden")
    def _onchange_garden(self):
        self.garden_area = 10 if self.garden else 0
        self.garden_orientation = "north" if self.garden else None

    def set_sold_state(self):
        if self.state == "sold":
            raise exceptions.UserError("Property has been already sold")
        if self.state == "canceled":
            raise exceptions.UserError("Canceled property cannot be sold")
        if self.state != "offer_received":
            raise exceptions.UserError("Accept offer first")
        self.state = "sold"
        return True

    def set_canceled_state(self):
        if self.state == "sold":
            raise exceptions.UserError("Sold property cannot be canceled")
        self.state = "canceled"
        for offer in self.offer_ids:
            offer.status = "refused"
        self.buyer_id = False
        self.selling_price = 0
        return True
