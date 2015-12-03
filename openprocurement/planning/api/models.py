# -*- coding: utf-8 -*-
from couchdb_schematics.document import SchematicsDocument
from datetime import timedelta
from pyramid.security import Allow
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, IntType, URLType, BooleanType, BaseType, FloatType
from schematics.types.compound import ModelType, DictType
from schematics.types.serializable import serializable
from uuid import uuid4
from zope.interface import implementer, Interface
from openprocurement.api.models import schematics_embedded_role, schematics_default_role, IsoDateTimeType, ListType
from openprocurement.api.models import Unit, CPVClassification, Classification, Identifier
from openprocurement.api.models import Model, Period, Revision
from openprocurement.api.models import validate_cpv_group, validate_items_uniq, validate_dkpp

STAND_STILL_TIME = timedelta(days=1)


class IPlan(Interface):
    """ Base plan marker interface """


def get_plan(model):
    while not isinstance(model, Plan):
        model = model.__parent__
    return model


class Project(Model):
    """A project."""

    id = StringType(required=True)
    name = StringType(required=True)


class Budget(Model):
    """A budget."""

    id = StringType(required=True)
    description = StringType(required=True)
    amount = FloatType(required=True)
    currency = StringType(required=False, default=u'UAH', max_length=3,
                          min_length=3)  # The currency in 3-letter ISO 4217 format.
    amountNet = FloatType()
    project = ModelType(Project)


class PlanItem(Model):
    """Simple item model for planing"""

    id = StringType(required=True, min_length=1, default=lambda: uuid4().hex)
    classification = ModelType(CPVClassification, required=True)
    additionalClassifications = ListType(ModelType(Classification), default=list(), required=True, min_size=1,
                                         validators=[validate_dkpp])
    unit = ModelType(Unit)  # Description of the unit which the good comes in e.g. hours, kilograms
    quantity = IntType()  # The number of units required
    deliveryDate = ModelType(Period)
    description = StringType(required=True)  # A description of the goods, services to be provided.


class PlanOrganization(Model):
    """An organization."""

    name = StringType(required=True)
    name_en = StringType()
    name_ru = StringType()
    identifier = ModelType(Identifier, required=True)


class PlanTender(Model):
    procurementMethod = StringType(choices=['open'], default='open', required=True)
    tenderPeriod = ModelType(Period, required=True)


plain_role = (blacklist('revisions', 'dateModified') + schematics_embedded_role)
create_role = (blacklist('owner_token', 'owner', 'revisions') + schematics_embedded_role)
edit_role = (
blacklist('owner_token', 'owner', 'revisions', 'dateModified', 'doc_id', 'planID') + schematics_embedded_role)
cancel_role = whitelist('status')
view_role = (blacklist('owner', 'owner_token', '_attachments', 'revisions') + schematics_embedded_role)
listing_role = whitelist('dateModified', 'doc_id')
Administrator_role = whitelist('status', 'mode', 'procuringEntity')


@implementer(IPlan)
class Plan(SchematicsDocument, Model):
    """Plan"""

    class Options:
        roles = {
            'plain': plain_role,
            'create': create_role,
            'edit': edit_role,
            'view': view_role,
            'listing': listing_role,
            'unsuccessful': view_role,
            'cancelled': view_role,
            'Administrator': Administrator_role,
            'default': schematics_default_role,
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'plan_owner')])

    # fields

    # procuringEntity:identifier:scheme *     Код Замовника -- Схема ідентификації по стандарту IATI, (наприклад код ЄДР - UA-EDR)
    # procuringEntity:identifier:id *         Для схеми UA-EDR - код ЄДРПОУ або ІПН
    # procuringEntity:name *                  Коротка назва организації (наприклад - ДУС)
    # procuringEntity:identifier:legalName *  Повна назва організації (наприклад - ДП “Державне Уравління Справами”)
    procuringEntity = ModelType(PlanOrganization, required=True)

    # tender:tenderPeriod:startDate           Планова дата старту процедури
    # tender:procurementMethod                Можливі варіанти: “open”
    tender = ModelType(PlanTender, required=True)

    # budget:project:name                     Назва проекту
    # budget:project:id                       Код проекту
    # budget:id *                             Комбінація budget:project:id  та items[*]:classification:id
    # budget:description *                    Довільний опис статті бюджету
    # budget:amount *                         Планова сума з ПДВ
    # budget:amountNet                        Планова сума без ПДВ
    budget = ModelType(Budget, required=True)

    classification = ModelType(CPVClassification, required=True)

    additionalClassifications = ListType(ModelType(Classification), default=list(), required=False)

    planID = StringType()
    mode = StringType(choices=['test'])  # flag for test data ?
    items = ListType(ModelType(PlanItem), required=False, min_size=1,
                     validators=[validate_cpv_group, validate_items_uniq])
    dateModified = IsoDateTimeType()
    owner_token = StringType()
    owner = StringType()
    procurementMethodType = StringType()
    revisions = ListType(ModelType(Revision), default=list())

    __name__ = ''

    def __acl__(self):
        acl = [
            # (Allow, '{}_{}'.format(i.owner, i.owner_token), 'create_award_complaint')
            # for i in self.bids
        ]
        acl.extend([
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_plan'),
        ])
        return acl

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [k for k in data.keys() if not data[k]]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self
