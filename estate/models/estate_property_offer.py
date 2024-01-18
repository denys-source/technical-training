from datetime import datetime, timedelta

from odoo import models, fields, api, exceptions


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offers"

    price = fields.Float()
    status = fields.Selection(
        selection=[("accepted", "Accepted"), ("refused", "Refused")],
        readonly=True,
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
        compute="_compute_deadline", inverse="_inverse_deadline"
    )

    @api.depends("validity")
    def _compute_deadline(self):
        for property in self:
            property.date_deadline = datetime.now() + timedelta(
                days=property.validity
            )

    def _inverse_deadline(self):
        for property in self:
            property.validity = (
                property.date_deadline - property.create_date.date()
            ).days

    def accept_offer(self):
        if self.status != "accepted":
            offers = self.search([])
            for offer in offers:
                offer.status = "refused"
            self.status = "accepted"
            self.property_id.state = "offer_received"
            self.property_id.write(
                {
                    "buyer_id": self.partner_id,
                    "selling_price": self.price,
                }
            )
        return True

    def refuse_offer(self):
        if self.status == "accepted":
            self.property_id.state = "new"
            self.property_id.write(
                {
                    "buyer_id": False,
                    "selling_price": 0,
                }
            )
        self.status = "refused"
        return True
