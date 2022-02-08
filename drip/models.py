from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.core.models import Orderable
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel


from drip.utils import get_user_model
from .types import (
    AbstractQuerySetRuleQuerySet,
    DateTime,
    BoolOrStr,
    FExpressionOrStr,
    TimeDeltaOrStr
)

# just using this to parse, but totally insane package naming...
# https://bitbucket.org/schinckel/django-timedelta-field/
from drip.helpers import parse


class AbstractDrip(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    lastchanged = models.DateTimeField(auto_now=True)
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Drip Name',
        help_text='A unique name for this drip.'
    )
    enabled = models.BooleanField(default=False)

    from_email = models.EmailField(
        null=True, blank=True, help_text='Set a custom from email.'
    )
    from_email_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        default=settings.EMAIL_ADMIN,
        help_text='Set a name for a custom from email.'
    )
    subject_template = models.TextField(null=True, blank=True)
    body_html_template = models.TextField(
        null=True,
        blank=True,
        help_text='You will have settings and user in the context.'
    )
    message_class = models.CharField(
        max_length=120, blank=True, default='default'
    )

    class Meta:
        abstract = True

    @property
    def drip(self):
        from drip.drips import DripBase

        drip = DripBase(
            drip_model=self,
            name=self.name,
            from_email=self.from_email if self.from_email else None,
            from_email_name=self.from_email_name if (
                self.from_email_name
            )
            else None,
            subject_template=self.subject_template if (
                self.subject_template
            )
            else None,
            body_template=self.body_html_template if (
                self.body_html_template
            )
            else None
        )
        return drip

    def __str__(self):
        return self.name


class Drip(AbstractDrip, ClusterableModel):
    body_html_template = models.TextField(
        null=True,
        blank=True,
        help_text='You have all of the user fields in the context. For example {{ first_name }} {{ last_name }} will return "Joe Smith".')
    panels = [
        FieldPanel('name'),
        FieldPanel('enabled'),
        FieldPanel('from_email'),
        FieldPanel('from_email_name'),
        FieldPanel('subject_template'),
        FieldPanel('body_html_template'),
        InlinePanel('queryset_rules'),
    ]

    class Meta:
        abstract = False
        app_label = 'drip'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class AbstractSentDrip(models.Model):
    """
    Keeps a record of all sent drips.
    """
    date = models.DateTimeField(auto_now_add=True)
    drip = models.ForeignKey(
        'drip.Drip',
        related_name='sent_drips',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        related_name='sent_drips',
        on_delete=models.CASCADE,
    )
    subject = models.TextField()
    body = models.TextField()
    from_email = models.EmailField(
        # For south so that it can migrate existing rows.
        null=True, default=None
    )
    from_email_name = models.CharField(
        max_length=150,
        # For south so that it can migrate existing rows.
        null=True,
        default=None
    )

    class Meta:
        abstract = True


class SentDrip(AbstractSentDrip):
    name = models.ForeignKey(
        'drip.Drip',
        null=True,
        to_field='name',
        db_column='name',
        on_delete=models.CASCADE,
    )


METHOD_TYPES = (
    ('filter', 'Filter'),
    ('exclude', 'Exclude'),
)

LOOKUP_TYPES = (
    ('exact', 'exactly'),
    ('iexact', 'exactly (case insensitive)'),
    ('contains', 'contains'),
    ('icontains', 'contains (case insensitive)'),
    ('regex', 'regex'),
    ('iregex', 'regex (case insensitive)'),
    ('gt', 'greater than'),
    ('gte', 'greater than or equal to'),
    ('lt', 'less than'),
    ('lte', 'less than or equal to'),
    ('startswith', 'starts with'),
    ('istartswith', 'starts with (case insensitive)'),
    ('endswith', 'ends with'),
    ('iendswith', 'ends with (case insensitive)'),
)

FIELD_NAMES = (
    ('id', 'id (AutoField)'),
    ('password', 'password (CharField)'),
    ('last_login', 'last_login (DateTimeField)'),
    ('is_superuser', 'is_superuser (BooleanField)'),
    ('first_name', 'first_name (CharField)'),
    ('last_name', 'last_name (CharField)'),
    ('is_staff', 'is_staff (BooleanField)'),
    ('is_active', 'is_active (BooleanField)'),
    ('date_joined', 'date_joined (DateTimeField)'),
    ('user_name', 'user_name (CharField)'),
    ('email', 'email (EmailField)'),
    ('is_mailsubscribed', 'is_mailsubscribed (BooleanField)'),
    ('is_paysubscribed', 'is_paysubscribed (PositiveSmallIntegerField)'),
    ('paysubscribe_changed', 'paysubscribe_changed (DateTimeField)'),
    ('is_smssubscribed', 'is_smssubscribed (BooleanField)'),
    ('is_newuserprofile', 'is_newuserprofile (BooleanField)'),
    ('stripe_customer', 'stripe_customer (ForeignKey)'),
    ('stripe_customer__user__djstripe_created', 'stripe_customer__user__djstripe_created (DateTimeField)'),
    ('stripe_customer__user__djstripe_updated', 'stripe_customer__user__djstripe_updated (DateTimeField)'),
    ('stripe_customer__user__djstripe_id', 'stripe_customer__user__djstripe_id (BigAutoField)'),
    ('stripe_customer__user__id', 'stripe_customer__user__id (StripeIdField)'),
    ('stripe_customer__user__djstripe_owner_account', 'stripe_customer__user__djstripe_owner_account (StripeForeignKey)'),
    ('stripe_customer__user__livemode', 'stripe_customer__user__livemode (BooleanField)'),
    ('stripe_customer__user__created', 'stripe_customer__user__created (StripeDateTimeField)'),
    ('stripe_customer__user__metadata', 'stripe_customer__user__metadata (JSONField)'),
    ('stripe_customer__user__description', 'stripe_customer__user__description (TextField)'),
    ('stripe_customer__user__address', 'stripe_customer__user__address (JSONField)'),
    ('stripe_customer__user__balance', 'stripe_customer__user__balance (StripeQuantumCurrencyAmountField)'),
    ('stripe_customer__user__currency', 'stripe_customer__user__currency (StripeCurrencyCodeField)'),
    ('stripe_customer__user__default_source', 'stripe_customer__user__default_source (PaymentMethodForeignKey)'),
    ('stripe_customer__user__delinquent', 'stripe_customer__user__delinquent (BooleanField)'),
    ('stripe_customer__user__coupon', 'stripe_customer__user__coupon (ForeignKey)'),
    ('stripe_customer__user__coupon_start', 'stripe_customer__user__coupon_start (StripeDateTimeField)'),
    ('stripe_customer__user__coupon_end', 'stripe_customer__user__coupon_end (StripeDateTimeField)'),
    ('stripe_customer__user__email', 'stripe_customer__user__email (TextField)'),
    ('stripe_customer__user__invoice_prefix', 'stripe_customer__user__invoice_prefix (CharField)'),
    ('stripe_customer__user__invoice_settings', 'stripe_customer__user__invoice_settings (JSONField)'),
    ('stripe_customer__user__default_payment_method', 'stripe_customer__user__default_payment_method (StripeForeignKey)'),
    ('stripe_customer__user__name', 'stripe_customer__user__name (TextField)'),
    ('stripe_customer__user__phone', 'stripe_customer__user__phone (TextField)'),
    ('stripe_customer__user__preferred_locales', 'stripe_customer__user__preferred_locales (JSONField)'),
    ('stripe_customer__user__shipping', 'stripe_customer__user__shipping (JSONField)'),
    ('stripe_customer__user__tax_exempt', 'stripe_customer__user__tax_exempt (StripeEnumField)'),
    ('stripe_customer__user__subscriber', 'stripe_customer__user__subscriber (ForeignKey)'),
    ('stripe_customer__user__date_purged', 'stripe_customer__user__date_purged (DateTimeField)'),
    ('stripe_customer__user__customuser', 'stripe_customer__user__customuser (ManyToOneRel)'),
    ('stripe_customer__user__invoices', 'stripe_customer__user__invoices (ManyToOneRel)'),
    ('stripe_customer__user__upcominginvoices', 'stripe_customer__user__upcominginvoices (ManyToOneRel)'),
    ('stripe_customer__user__invoiceitems', 'stripe_customer__user__invoiceitems (ManyToOneRel)'),
    ('stripe_customer__user__subscriptions', 'stripe_customer__user__subscriptions (ManyToOneRel)'),
    ('stripe_customer__user__schedules', 'stripe_customer__user__schedules (ManyToOneRel)'),
    ('stripe_customer__user__tax_ids', 'stripe_customer__user__tax_ids (ManyToOneRel)'),
    ('stripe_customer__user__session', 'stripe_customer__user__session (ManyToOneRel)'),
    ('stripe_customer__user__charges', 'stripe_customer__user__charges (ManyToOneRel)'),
    ('stripe_customer__user__paymentintent', 'stripe_customer__user__paymentintent (ManyToOneRel)'),
    ('stripe_customer__user__setupintent', 'stripe_customer__user__setupintent (ManyToOneRel)'),
    ('stripe_customer__user__bank_account', 'stripe_customer__user__bank_account (ManyToOneRel)'),
    ('stripe_customer__user__legacy_cards', 'stripe_customer__user__legacy_cards (ManyToOneRel)'),
    ('stripe_customer__user__sources', 'stripe_customer__user__sources (ManyToOneRel)'),
    ('stripe_customer__user__payment_methods', 'stripe_customer__user__payment_methods (ManyToOneRel)'),
    ('stripe_subscription', 'stripe_subscription (ForeignKey)'),
    ('stripe_subscription__user__djstripe_created', 'stripe_subscription__user__djstripe_created (DateTimeField)'),
    ('stripe_subscription__user__djstripe_updated', 'stripe_subscription__user__djstripe_updated (DateTimeField)'),
    ('stripe_subscription__user__djstripe_id', 'stripe_subscription__user__djstripe_id (BigAutoField)'),
    ('stripe_subscription__user__id', 'stripe_subscription__user__id (StripeIdField)'),
    ('stripe_subscription__user__djstripe_owner_account', 'stripe_subscription__user__djstripe_owner_account (StripeForeignKey)'),
    ('stripe_subscription__user__livemode', 'stripe_subscription__user__livemode (BooleanField)'),
    ('stripe_subscription__user__created', 'stripe_subscription__user__created (StripeDateTimeField)'),
    ('stripe_subscription__user__metadata', 'stripe_subscription__user__metadata (JSONField)'),
    ('stripe_subscription__user__description', 'stripe_subscription__user__description (TextField)'),
    ('stripe_subscription__user__application_fee_percent', 'stripe_subscription__user__application_fee_percent (StripePercentField)'),
    ('stripe_subscription__user__billing_cycle_anchor', 'stripe_subscription__user__billing_cycle_anchor (StripeDateTimeField)'),
    ('stripe_subscription__user__billing_thresholds', 'stripe_subscription__user__billing_thresholds (JSONField)'),
    ('stripe_subscription__user__cancel_at', 'stripe_subscription__user__cancel_at (StripeDateTimeField)'),
    ('stripe_subscription__user__cancel_at_period_end', 'stripe_subscription__user__cancel_at_period_end (BooleanField)'),
    ('stripe_subscription__user__canceled_at', 'stripe_subscription__user__canceled_at (StripeDateTimeField)'),
    ('stripe_subscription__user__collection_method', 'stripe_subscription__user__collection_method (StripeEnumField)'),
    ('stripe_subscription__user__current_period_end', 'stripe_subscription__user__current_period_end (StripeDateTimeField)'),
    ('stripe_subscription__user__current_period_start', 'stripe_subscription__user__current_period_start (StripeDateTimeField)'),
    ('stripe_subscription__user__customer', 'stripe_subscription__user__customer (StripeForeignKey)'),
    ('stripe_subscription__user__days_until_due', 'stripe_subscription__user__days_until_due (IntegerField)'),
    ('stripe_subscription__user__default_payment_method', 'stripe_subscription__user__default_payment_method (StripeForeignKey)'),
    ('stripe_subscription__user__default_source', 'stripe_subscription__user__default_source (PaymentMethodForeignKey)'),
    ('stripe_subscription__user__discount', 'stripe_subscription__user__discount (JSONField)'),
    ('stripe_subscription__user__ended_at', 'stripe_subscription__user__ended_at (StripeDateTimeField)'),
    ('stripe_subscription__user__next_pending_invoice_item_invoice', 'stripe_subscription__user__next_pending_invoice_item_invoice (StripeDateTimeField)'),
    ('stripe_subscription__user__pending_invoice_item_interval', 'stripe_subscription__user__pending_invoice_item_interval (JSONField)'),
    ('stripe_subscription__user__pending_setup_intent', 'stripe_subscription__user__pending_setup_intent (StripeForeignKey)'),
    ('stripe_subscription__user__pending_update', 'stripe_subscription__user__pending_update (JSONField)'),
    ('stripe_subscription__user__plan', 'stripe_subscription__user__plan (ForeignKey)'),
    ('stripe_subscription__user__quantity', 'stripe_subscription__user__quantity (IntegerField)'),
    ('stripe_subscription__user__schedule', 'stripe_subscription__user__schedule (ForeignKey)'),
    ('stripe_subscription__user__start_date', 'stripe_subscription__user__start_date (StripeDateTimeField)'),
    ('stripe_subscription__user__status', 'stripe_subscription__user__status (StripeEnumField)'),
    ('stripe_subscription__user__trial_end', 'stripe_subscription__user__trial_end (StripeDateTimeField)'),
    ('stripe_subscription__user__trial_start', 'stripe_subscription__user__trial_start (StripeDateTimeField)'),
    ('stripe_subscription__user__default_tax_rates', 'stripe_subscription__user__default_tax_rates (ManyToManyField)'),
    ('stripe_subscription__user__customuser', 'stripe_subscription__user__customuser (ManyToOneRel)'),
    ('stripe_subscription__user__invoices', 'stripe_subscription__user__invoices (ManyToOneRel)'),
    ('stripe_subscription__user__upcominginvoices', 'stripe_subscription__user__upcominginvoices (ManyToOneRel)'),
    ('stripe_subscription__user__invoiceitems', 'stripe_subscription__user__invoiceitems (ManyToOneRel)'),
    ('stripe_subscription__user__items', 'stripe_subscription__user__items (ManyToOneRel)'),
    ('stripe_subscription__user__released_schedules', 'stripe_subscription__user__released_schedules (ManyToOneRel)'),
    ('stripe_subscription__user__session', 'stripe_subscription__user__session (ManyToOneRel)'),
    ('stripe_paymentmethod', 'stripe_paymentmethod (ForeignKey)'),
    ('stripe_paymentmethod__user__djstripe_created', 'stripe_paymentmethod__user__djstripe_created (DateTimeField)'),
    ('stripe_paymentmethod__user__djstripe_updated', 'stripe_paymentmethod__user__djstripe_updated (DateTimeField)'),
    ('stripe_paymentmethod__user__djstripe_id', 'stripe_paymentmethod__user__djstripe_id (BigAutoField)'),
    ('stripe_paymentmethod__user__id', 'stripe_paymentmethod__user__id (StripeIdField)'),
    ('stripe_paymentmethod__user__djstripe_owner_account', 'stripe_paymentmethod__user__djstripe_owner_account (StripeForeignKey)'),
    ('stripe_paymentmethod__user__livemode', 'stripe_paymentmethod__user__livemode (BooleanField)'),
    ('stripe_paymentmethod__user__created', 'stripe_paymentmethod__user__created (StripeDateTimeField)'),
    ('stripe_paymentmethod__user__metadata', 'stripe_paymentmethod__user__metadata (JSONField)'),
    ('stripe_paymentmethod__user__billing_details', 'stripe_paymentmethod__user__billing_details (JSONField)'),
    ('stripe_paymentmethod__user__customer', 'stripe_paymentmethod__user__customer (StripeForeignKey)'),
    ('stripe_paymentmethod__user__type', 'stripe_paymentmethod__user__type (StripeEnumField)'),
    ('stripe_paymentmethod__user__alipay', 'stripe_paymentmethod__user__alipay (JSONField)'),
    ('stripe_paymentmethod__user__au_becs_debit', 'stripe_paymentmethod__user__au_becs_debit (JSONField)'),
    ('stripe_paymentmethod__user__bacs_debit', 'stripe_paymentmethod__user__bacs_debit (JSONField)'),
    ('stripe_paymentmethod__user__bancontact', 'stripe_paymentmethod__user__bancontact (JSONField)'),
    ('stripe_paymentmethod__user__card', 'stripe_paymentmethod__user__card (JSONField)'),
    ('stripe_paymentmethod__user__card_present', 'stripe_paymentmethod__user__card_present (JSONField)'),
    ('stripe_paymentmethod__user__eps', 'stripe_paymentmethod__user__eps (JSONField)'),
    ('stripe_paymentmethod__user__fpx', 'stripe_paymentmethod__user__fpx (JSONField)'),
    ('stripe_paymentmethod__user__giropay', 'stripe_paymentmethod__user__giropay (JSONField)'),
    ('stripe_paymentmethod__user__ideal', 'stripe_paymentmethod__user__ideal (JSONField)'),
    ('stripe_paymentmethod__user__interac_present', 'stripe_paymentmethod__user__interac_present (JSONField)'),
    ('stripe_paymentmethod__user__oxxo', 'stripe_paymentmethod__user__oxxo (JSONField)'),
    ('stripe_paymentmethod__user__p24', 'stripe_paymentmethod__user__p24 (JSONField)'),
    ('stripe_paymentmethod__user__sepa_debit', 'stripe_paymentmethod__user__sepa_debit (JSONField)'),
    ('stripe_paymentmethod__user__sofort', 'stripe_paymentmethod__user__sofort (JSONField)'),
    ('stripe_paymentmethod__user__customuser', 'stripe_paymentmethod__user__customuser (ManyToOneRel)'),
    ('stripe_paymentmethod__user__charges', 'stripe_paymentmethod__user__charges (ManyToOneRel)'),
    ('stripe_paymentmethod__user__mandate', 'stripe_paymentmethod__user__mandate (ManyToOneRel)'),
    ('stripe_paymentmethod__user__paymentintent', 'stripe_paymentmethod__user__paymentintent (ManyToOneRel)'),
    ('stripe_paymentmethod__user__setupintent', 'stripe_paymentmethod__user__setupintent (ManyToOneRel)'),
    ('groups', 'groups (ManyToManyField)'),
    ('groups__user__id', 'groups__user__id (AutoField)'),
    ('groups__user__name', 'groups__user__name (CharField)'),
    ('groups__user__user', 'groups__user__user (ManyToManyRel)'),
    ('groups__user__pageviewrestriction', 'groups__user__pageviewrestriction (ManyToManyRel)'),
    ('groups__user__collectionviewrestriction', 'groups__user__collectionviewrestriction (ManyToManyRel)'),
    ('groups__user__groupapprovaltask', 'groups__user__groupapprovaltask (ManyToManyRel)'),
    ('groups__user__email', 'groups__user__email (ManyToOneRel)'),
    ('base_userprofile', 'base_userprofile (OneToOneRel)'),
    ('base_userprofile__user__id', 'base_userprofile__user__id (AutoField)'),
    ('base_userprofile__user__password', 'base_userprofile__user__password (CharField)'),
    ('base_userprofile__user__last_login', 'base_userprofile__user__last_login (DateTimeField)'),
    ('base_userprofile__user__is_superuser', 'base_userprofile__user__is_superuser (BooleanField)'),
    ('base_userprofile__user__first_name', 'base_userprofile__user__first_name (CharField)'),
    ('base_userprofile__user__last_name', 'base_userprofile__user__last_name (CharField)'),
    ('base_userprofile__user__is_staff', 'base_userprofile__user__is_staff (BooleanField)'),
    ('base_userprofile__user__is_active', 'base_userprofile__user__is_active (BooleanField)'),
    ('base_userprofile__user__date_joined', 'base_userprofile__user__date_joined (DateTimeField)'),
    ('base_userprofile__user__user_name', 'base_userprofile__user__user_name (CharField)'),
    ('base_userprofile__user__email', 'base_userprofile__user__email (EmailField)'),
    ('base_userprofile__user__is_mailsubscribed', 'base_userprofile__user__is_mailsubscribed (BooleanField)'),
    ('base_userprofile__user__is_paysubscribed', 'base_userprofile__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('base_userprofile__user__paysubscribe_changed', 'base_userprofile__user__paysubscribe_changed (DateTimeField)'),
    ('base_userprofile__user__is_smssubscribed', 'base_userprofile__user__is_smssubscribed (BooleanField)'),
    ('base_userprofile__user__is_newuserprofile', 'base_userprofile__user__is_newuserprofile (BooleanField)'),
    ('base_userprofile__user__stripe_customer', 'base_userprofile__user__stripe_customer (ForeignKey)'),
    ('base_userprofile__user__stripe_subscription', 'base_userprofile__user__stripe_subscription (ForeignKey)'),
    ('base_userprofile__user__stripe_paymentmethod', 'base_userprofile__user__stripe_paymentmethod (ForeignKey)'),
    ('base_userprofile__user__uuid', 'base_userprofile__user__uuid (UUIDField)'),
    ('base_userprofile__user__groups', 'base_userprofile__user__groups (ManyToManyField)'),
    ('base_userprofile__user__base_userprofile', 'base_userprofile__user__base_userprofile (OneToOneRel)'),
    ('base_userprofile__user__custommedia', 'base_userprofile__user__custommedia (ManyToOneRel)'),
    ('base_userprofile__user__podcastcontentindexpage', 'base_userprofile__user__podcastcontentindexpage (ManyToOneRel)'),
    ('base_userprofile__user__segment', 'base_userprofile__user__segment (ManyToManyRel)'),
    ('base_userprofile__user__excluded_segments', 'base_userprofile__user__excluded_segments (ManyToManyRel)'),
    ('base_userprofile__user__wagtail_userprofile', 'base_userprofile__user__wagtail_userprofile (OneToOneRel)'),
    ('base_userprofile__user__document', 'base_userprofile__user__document (ManyToOneRel)'),
    ('base_userprofile__user__uploadeddocument', 'base_userprofile__user__uploadeddocument (ManyToOneRel)'),
    ('base_userprofile__user__image', 'base_userprofile__user__image (ManyToOneRel)'),
    ('base_userprofile__user__uploadedimage', 'base_userprofile__user__uploadedimage (ManyToOneRel)'),
    ('base_userprofile__user__owned_pages', 'base_userprofile__user__owned_pages (ManyToOneRel)'),
    ('base_userprofile__user__locked_pages', 'base_userprofile__user__locked_pages (ManyToOneRel)'),
    ('base_userprofile__user__pagerevision', 'base_userprofile__user__pagerevision (ManyToOneRel)'),
    ('base_userprofile__user__requested_workflows', 'base_userprofile__user__requested_workflows (ManyToOneRel)'),
    ('base_userprofile__user__finished_task_states', 'base_userprofile__user__finished_task_states (ManyToOneRel)'),
    ('base_userprofile__user__emailaddress', 'base_userprofile__user__emailaddress (ManyToOneRel)'),
    ('base_userprofile__user__socialaccount', 'base_userprofile__user__socialaccount (ManyToOneRel)'),
    ('base_userprofile__user__media', 'base_userprofile__user__media (ManyToOneRel)'),
    ('base_userprofile__user__sent_drips', 'base_userprofile__user__sent_drips (ManyToOneRel)'),
    ('base_userprofile__user__djstripe_customers', 'base_userprofile__user__djstripe_customers (ManyToOneRel)'),
    ('base_userprofile__user__reactions', 'base_userprofile__user__reactions (ManyToOneRel)'),
    ('base_userprofile__user__flags_moderated', 'base_userprofile__user__flags_moderated (ManyToOneRel)'),
    ('base_userprofile__user__flags', 'base_userprofile__user__flags (ManyToOneRel)'),
    ('base_userprofile__user__blockeduser', 'base_userprofile__user__blockeduser (ManyToOneRel)'),
    ('base_userprofile__user__blockeduserhistory', 'base_userprofile__user__blockeduserhistory (ManyToOneRel)'),
    ('base_userprofile__user__logentry', 'base_userprofile__user__logentry (ManyToOneRel)'),
    ('base_userprofile__user__totpdevice', 'base_userprofile__user__totpdevice (ManyToOneRel)'),
    ('base_userprofile__user__staticdevice', 'base_userprofile__user__staticdevice (ManyToOneRel)'),
    ('segment', 'segment (ManyToManyRel)'),
    ('segment__user__id', 'segment__user__id (AutoField)'),
    ('segment__user__password', 'segment__user__password (CharField)'),
    ('segment__user__last_login', 'segment__user__last_login (DateTimeField)'),
    ('segment__user__is_superuser', 'segment__user__is_superuser (BooleanField)'),
    ('segment__user__first_name', 'segment__user__first_name (CharField)'),
    ('segment__user__last_name', 'segment__user__last_name (CharField)'),
    ('segment__user__is_staff', 'segment__user__is_staff (BooleanField)'),
    ('segment__user__is_active', 'segment__user__is_active (BooleanField)'),
    ('segment__user__date_joined', 'segment__user__date_joined (DateTimeField)'),
    ('segment__user__user_name', 'segment__user__user_name (CharField)'),
    ('segment__user__email', 'segment__user__email (EmailField)'),
    ('segment__user__is_mailsubscribed', 'segment__user__is_mailsubscribed (BooleanField)'),
    ('segment__user__is_paysubscribed', 'segment__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('segment__user__paysubscribe_changed', 'segment__user__paysubscribe_changed (DateTimeField)'),
    ('segment__user__is_smssubscribed', 'segment__user__is_smssubscribed (BooleanField)'),
    ('segment__user__is_newuserprofile', 'segment__user__is_newuserprofile (BooleanField)'),
    ('segment__user__stripe_customer', 'segment__user__stripe_customer (ForeignKey)'),
    ('segment__user__stripe_subscription', 'segment__user__stripe_subscription (ForeignKey)'),
    ('segment__user__stripe_paymentmethod', 'segment__user__stripe_paymentmethod (ForeignKey)'),
    ('segment__user__uuid', 'segment__user__uuid (UUIDField)'),
    ('segment__user__groups', 'segment__user__groups (ManyToManyField)'),
    ('segment__user__base_userprofile', 'segment__user__base_userprofile (OneToOneRel)'),
    ('segment__user__custommedia', 'segment__user__custommedia (ManyToOneRel)'),
    ('segment__user__podcastcontentindexpage', 'segment__user__podcastcontentindexpage (ManyToOneRel)'),
    ('segment__user__segment', 'segment__user__segment (ManyToManyRel)'),
    ('segment__user__excluded_segments', 'segment__user__excluded_segments (ManyToManyRel)'),
    ('segment__user__wagtail_userprofile', 'segment__user__wagtail_userprofile (OneToOneRel)'),
    ('segment__user__document', 'segment__user__document (ManyToOneRel)'),
    ('segment__user__uploadeddocument', 'segment__user__uploadeddocument (ManyToOneRel)'),
    ('segment__user__image', 'segment__user__image (ManyToOneRel)'),
    ('segment__user__uploadedimage', 'segment__user__uploadedimage (ManyToOneRel)'),
    ('segment__user__owned_pages', 'segment__user__owned_pages (ManyToOneRel)'),
    ('segment__user__locked_pages', 'segment__user__locked_pages (ManyToOneRel)'),
    ('segment__user__pagerevision', 'segment__user__pagerevision (ManyToOneRel)'),
    ('segment__user__requested_workflows', 'segment__user__requested_workflows (ManyToOneRel)'),
    ('segment__user__finished_task_states', 'segment__user__finished_task_states (ManyToOneRel)'),
    ('segment__user__emailaddress', 'segment__user__emailaddress (ManyToOneRel)'),
    ('segment__user__socialaccount', 'segment__user__socialaccount (ManyToOneRel)'),
    ('segment__user__media', 'segment__user__media (ManyToOneRel)'),
    ('segment__user__sent_drips', 'segment__user__sent_drips (ManyToOneRel)'),
    ('segment__user__djstripe_customers', 'segment__user__djstripe_customers (ManyToOneRel)'),
    ('segment__user__reactions', 'segment__user__reactions (ManyToOneRel)'),
    ('segment__user__flags_moderated', 'segment__user__flags_moderated (ManyToOneRel)'),
    ('segment__user__flags', 'segment__user__flags (ManyToOneRel)'),
    ('segment__user__blockeduser', 'segment__user__blockeduser (ManyToOneRel)'),
    ('segment__user__blockeduserhistory', 'segment__user__blockeduserhistory (ManyToOneRel)'),
    ('segment__user__logentry', 'segment__user__logentry (ManyToOneRel)'),
    ('segment__user__totpdevice', 'segment__user__totpdevice (ManyToOneRel)'),
    ('segment__user__staticdevice', 'segment__user__staticdevice (ManyToOneRel)'),
    ('excluded_segments', 'excluded_segments (ManyToManyRel)'),
    ('excluded_segments__user__id', 'excluded_segments__user__id (AutoField)'),
    ('excluded_segments__user__password', 'excluded_segments__user__password (CharField)'),
    ('excluded_segments__user__last_login', 'excluded_segments__user__last_login (DateTimeField)'),
    ('excluded_segments__user__is_superuser', 'excluded_segments__user__is_superuser (BooleanField)'),
    ('excluded_segments__user__first_name', 'excluded_segments__user__first_name (CharField)'),
    ('excluded_segments__user__last_name', 'excluded_segments__user__last_name (CharField)'),
    ('excluded_segments__user__is_staff', 'excluded_segments__user__is_staff (BooleanField)'),
    ('excluded_segments__user__is_active', 'excluded_segments__user__is_active (BooleanField)'),
    ('excluded_segments__user__date_joined', 'excluded_segments__user__date_joined (DateTimeField)'),
    ('excluded_segments__user__user_name', 'excluded_segments__user__user_name (CharField)'),
    ('excluded_segments__user__email', 'excluded_segments__user__email (EmailField)'),
    ('excluded_segments__user__is_mailsubscribed', 'excluded_segments__user__is_mailsubscribed (BooleanField)'),
    ('excluded_segments__user__is_paysubscribed', 'excluded_segments__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('excluded_segments__user__paysubscribe_changed', 'excluded_segments__user__paysubscribe_changed (DateTimeField)'),
    ('excluded_segments__user__is_smssubscribed', 'excluded_segments__user__is_smssubscribed (BooleanField)'),
    ('excluded_segments__user__is_newuserprofile', 'excluded_segments__user__is_newuserprofile (BooleanField)'),
    ('excluded_segments__user__stripe_customer', 'excluded_segments__user__stripe_customer (ForeignKey)'),
    ('excluded_segments__user__stripe_subscription', 'excluded_segments__user__stripe_subscription (ForeignKey)'),
    ('excluded_segments__user__stripe_paymentmethod', 'excluded_segments__user__stripe_paymentmethod (ForeignKey)'),
    ('excluded_segments__user__uuid', 'excluded_segments__user__uuid (UUIDField)'),
    ('excluded_segments__user__groups', 'excluded_segments__user__groups (ManyToManyField)'),
    ('excluded_segments__user__base_userprofile', 'excluded_segments__user__base_userprofile (OneToOneRel)'),
    ('excluded_segments__user__custommedia', 'excluded_segments__user__custommedia (ManyToOneRel)'),
    ('excluded_segments__user__podcastcontentindexpage', 'excluded_segments__user__podcastcontentindexpage (ManyToOneRel)'),
    ('excluded_segments__user__segment', 'excluded_segments__user__segment (ManyToManyRel)'),
    ('excluded_segments__user__excluded_segments', 'excluded_segments__user__excluded_segments (ManyToManyRel)'),
    ('excluded_segments__user__wagtail_userprofile', 'excluded_segments__user__wagtail_userprofile (OneToOneRel)'),
    ('excluded_segments__user__document', 'excluded_segments__user__document (ManyToOneRel)'),
    ('excluded_segments__user__uploadeddocument', 'excluded_segments__user__uploadeddocument (ManyToOneRel)'),
    ('excluded_segments__user__image', 'excluded_segments__user__image (ManyToOneRel)'),
    ('excluded_segments__user__uploadedimage', 'excluded_segments__user__uploadedimage (ManyToOneRel)'),
    ('excluded_segments__user__owned_pages', 'excluded_segments__user__owned_pages (ManyToOneRel)'),
    ('excluded_segments__user__locked_pages', 'excluded_segments__user__locked_pages (ManyToOneRel)'),
    ('excluded_segments__user__pagerevision', 'excluded_segments__user__pagerevision (ManyToOneRel)'),
    ('excluded_segments__user__requested_workflows', 'excluded_segments__user__requested_workflows (ManyToOneRel)'),
    ('excluded_segments__user__finished_task_states', 'excluded_segments__user__finished_task_states (ManyToOneRel)'),
    ('excluded_segments__user__emailaddress', 'excluded_segments__user__emailaddress (ManyToOneRel)'),
    ('excluded_segments__user__socialaccount', 'excluded_segments__user__socialaccount (ManyToOneRel)'),
    ('excluded_segments__user__media', 'excluded_segments__user__media (ManyToOneRel)'),
    ('excluded_segments__user__sent_drips', 'excluded_segments__user__sent_drips (ManyToOneRel)'),
    ('excluded_segments__user__djstripe_customers', 'excluded_segments__user__djstripe_customers (ManyToOneRel)'),
    ('excluded_segments__user__reactions', 'excluded_segments__user__reactions (ManyToOneRel)'),
    ('excluded_segments__user__flags_moderated', 'excluded_segments__user__flags_moderated (ManyToOneRel)'),
    ('excluded_segments__user__flags', 'excluded_segments__user__flags (ManyToOneRel)'),
    ('excluded_segments__user__blockeduser', 'excluded_segments__user__blockeduser (ManyToOneRel)'),
    ('excluded_segments__user__blockeduserhistory', 'excluded_segments__user__blockeduserhistory (ManyToOneRel)'),
    ('excluded_segments__user__logentry', 'excluded_segments__user__logentry (ManyToOneRel)'),
    ('excluded_segments__user__totpdevice', 'excluded_segments__user__totpdevice (ManyToOneRel)'),
    ('excluded_segments__user__staticdevice', 'excluded_segments__user__staticdevice (ManyToOneRel)'),
    ('wagtail_userprofile', 'wagtail_userprofile (OneToOneRel)'),
    ('wagtail_userprofile__user__id', 'wagtail_userprofile__user__id (AutoField)'),
    ('wagtail_userprofile__user__password', 'wagtail_userprofile__user__password (CharField)'),
    ('wagtail_userprofile__user__last_login', 'wagtail_userprofile__user__last_login (DateTimeField)'),
    ('wagtail_userprofile__user__is_superuser', 'wagtail_userprofile__user__is_superuser (BooleanField)'),
    ('wagtail_userprofile__user__first_name', 'wagtail_userprofile__user__first_name (CharField)'),
    ('wagtail_userprofile__user__last_name', 'wagtail_userprofile__user__last_name (CharField)'),
    ('wagtail_userprofile__user__is_staff', 'wagtail_userprofile__user__is_staff (BooleanField)'),
    ('wagtail_userprofile__user__is_active', 'wagtail_userprofile__user__is_active (BooleanField)'),
    ('wagtail_userprofile__user__date_joined', 'wagtail_userprofile__user__date_joined (DateTimeField)'),
    ('wagtail_userprofile__user__user_name', 'wagtail_userprofile__user__user_name (CharField)'),
    ('wagtail_userprofile__user__email', 'wagtail_userprofile__user__email (EmailField)'),
    ('wagtail_userprofile__user__is_mailsubscribed', 'wagtail_userprofile__user__is_mailsubscribed (BooleanField)'),
    ('wagtail_userprofile__user__is_paysubscribed', 'wagtail_userprofile__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('wagtail_userprofile__user__paysubscribe_changed', 'wagtail_userprofile__user__paysubscribe_changed (DateTimeField)'),
    ('wagtail_userprofile__user__is_smssubscribed', 'wagtail_userprofile__user__is_smssubscribed (BooleanField)'),
    ('wagtail_userprofile__user__is_newuserprofile', 'wagtail_userprofile__user__is_newuserprofile (BooleanField)'),
    ('wagtail_userprofile__user__stripe_customer', 'wagtail_userprofile__user__stripe_customer (ForeignKey)'),
    ('wagtail_userprofile__user__stripe_subscription', 'wagtail_userprofile__user__stripe_subscription (ForeignKey)'),
    ('wagtail_userprofile__user__stripe_paymentmethod', 'wagtail_userprofile__user__stripe_paymentmethod (ForeignKey)'),
    ('wagtail_userprofile__user__uuid', 'wagtail_userprofile__user__uuid (UUIDField)'),
    ('wagtail_userprofile__user__groups', 'wagtail_userprofile__user__groups (ManyToManyField)'),
    ('wagtail_userprofile__user__base_userprofile', 'wagtail_userprofile__user__base_userprofile (OneToOneRel)'),
    ('wagtail_userprofile__user__custommedia', 'wagtail_userprofile__user__custommedia (ManyToOneRel)'),
    ('wagtail_userprofile__user__podcastcontentindexpage', 'wagtail_userprofile__user__podcastcontentindexpage (ManyToOneRel)'),
    ('wagtail_userprofile__user__segment', 'wagtail_userprofile__user__segment (ManyToManyRel)'),
    ('wagtail_userprofile__user__excluded_segments', 'wagtail_userprofile__user__excluded_segments (ManyToManyRel)'),
    ('wagtail_userprofile__user__wagtail_userprofile', 'wagtail_userprofile__user__wagtail_userprofile (OneToOneRel)'),
    ('wagtail_userprofile__user__document', 'wagtail_userprofile__user__document (ManyToOneRel)'),
    ('wagtail_userprofile__user__uploadeddocument', 'wagtail_userprofile__user__uploadeddocument (ManyToOneRel)'),
    ('wagtail_userprofile__user__image', 'wagtail_userprofile__user__image (ManyToOneRel)'),
    ('wagtail_userprofile__user__uploadedimage', 'wagtail_userprofile__user__uploadedimage (ManyToOneRel)'),
    ('wagtail_userprofile__user__owned_pages', 'wagtail_userprofile__user__owned_pages (ManyToOneRel)'),
    ('wagtail_userprofile__user__locked_pages', 'wagtail_userprofile__user__locked_pages (ManyToOneRel)'),
    ('wagtail_userprofile__user__pagerevision', 'wagtail_userprofile__user__pagerevision (ManyToOneRel)'),
    ('wagtail_userprofile__user__requested_workflows', 'wagtail_userprofile__user__requested_workflows (ManyToOneRel)'),
    ('wagtail_userprofile__user__finished_task_states', 'wagtail_userprofile__user__finished_task_states (ManyToOneRel)'),
    ('wagtail_userprofile__user__emailaddress', 'wagtail_userprofile__user__emailaddress (ManyToOneRel)'),
    ('wagtail_userprofile__user__socialaccount', 'wagtail_userprofile__user__socialaccount (ManyToOneRel)'),
    ('wagtail_userprofile__user__media', 'wagtail_userprofile__user__media (ManyToOneRel)'),
    ('wagtail_userprofile__user__sent_drips', 'wagtail_userprofile__user__sent_drips (ManyToOneRel)'),
    ('wagtail_userprofile__user__djstripe_customers', 'wagtail_userprofile__user__djstripe_customers (ManyToOneRel)'),
    ('wagtail_userprofile__user__reactions', 'wagtail_userprofile__user__reactions (ManyToOneRel)'),
    ('wagtail_userprofile__user__flags_moderated', 'wagtail_userprofile__user__flags_moderated (ManyToOneRel)'),
    ('wagtail_userprofile__user__flags', 'wagtail_userprofile__user__flags (ManyToOneRel)'),
    ('wagtail_userprofile__user__blockeduser', 'wagtail_userprofile__user__blockeduser (ManyToOneRel)'),
    ('wagtail_userprofile__user__blockeduserhistory', 'wagtail_userprofile__user__blockeduserhistory (ManyToOneRel)'),
    ('wagtail_userprofile__user__logentry', 'wagtail_userprofile__user__logentry (ManyToOneRel)'),
    ('wagtail_userprofile__user__totpdevice', 'wagtail_userprofile__user__totpdevice (ManyToOneRel)'),
    ('wagtail_userprofile__user__staticdevice', 'wagtail_userprofile__user__staticdevice (ManyToOneRel)'),
    ('socialaccount', 'socialaccount (ManyToOneRel)'),
    ('socialaccount__user__id', 'socialaccount__user__id (AutoField)'),
    ('socialaccount__user__password', 'socialaccount__user__password (CharField)'),
    ('socialaccount__user__last_login', 'socialaccount__user__last_login (DateTimeField)'),
    ('socialaccount__user__is_superuser', 'socialaccount__user__is_superuser (BooleanField)'),
    ('socialaccount__user__first_name', 'socialaccount__user__first_name (CharField)'),
    ('socialaccount__user__last_name', 'socialaccount__user__last_name (CharField)'),
    ('socialaccount__user__is_staff', 'socialaccount__user__is_staff (BooleanField)'),
    ('socialaccount__user__is_active', 'socialaccount__user__is_active (BooleanField)'),
    ('socialaccount__user__date_joined', 'socialaccount__user__date_joined (DateTimeField)'),
    ('socialaccount__user__user_name', 'socialaccount__user__user_name (CharField)'),
    ('socialaccount__user__email', 'socialaccount__user__email (EmailField)'),
    ('socialaccount__user__is_mailsubscribed', 'socialaccount__user__is_mailsubscribed (BooleanField)'),
    ('socialaccount__user__is_paysubscribed', 'socialaccount__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('socialaccount__user__paysubscribe_changed', 'socialaccount__user__paysubscribe_changed (DateTimeField)'),
    ('socialaccount__user__is_smssubscribed', 'socialaccount__user__is_smssubscribed (BooleanField)'),
    ('socialaccount__user__is_newuserprofile', 'socialaccount__user__is_newuserprofile (BooleanField)'),
    ('socialaccount__user__stripe_customer', 'socialaccount__user__stripe_customer (ForeignKey)'),
    ('socialaccount__user__stripe_subscription', 'socialaccount__user__stripe_subscription (ForeignKey)'),
    ('socialaccount__user__stripe_paymentmethod', 'socialaccount__user__stripe_paymentmethod (ForeignKey)'),
    ('socialaccount__user__uuid', 'socialaccount__user__uuid (UUIDField)'),
    ('socialaccount__user__groups', 'socialaccount__user__groups (ManyToManyField)'),
    ('socialaccount__user__base_userprofile', 'socialaccount__user__base_userprofile (OneToOneRel)'),
    ('socialaccount__user__custommedia', 'socialaccount__user__custommedia (ManyToOneRel)'),
    ('socialaccount__user__podcastcontentindexpage', 'socialaccount__user__podcastcontentindexpage (ManyToOneRel)'),
    ('socialaccount__user__segment', 'socialaccount__user__segment (ManyToManyRel)'),
    ('socialaccount__user__excluded_segments', 'socialaccount__user__excluded_segments (ManyToManyRel)'),
    ('socialaccount__user__wagtail_userprofile', 'socialaccount__user__wagtail_userprofile (OneToOneRel)'),
    ('socialaccount__user__document', 'socialaccount__user__document (ManyToOneRel)'),
    ('socialaccount__user__uploadeddocument', 'socialaccount__user__uploadeddocument (ManyToOneRel)'),
    ('socialaccount__user__image', 'socialaccount__user__image (ManyToOneRel)'),
    ('socialaccount__user__uploadedimage', 'socialaccount__user__uploadedimage (ManyToOneRel)'),
    ('socialaccount__user__owned_pages', 'socialaccount__user__owned_pages (ManyToOneRel)'),
    ('socialaccount__user__locked_pages', 'socialaccount__user__locked_pages (ManyToOneRel)'),
    ('socialaccount__user__pagerevision', 'socialaccount__user__pagerevision (ManyToOneRel)'),
    ('socialaccount__user__requested_workflows', 'socialaccount__user__requested_workflows (ManyToOneRel)'),
    ('socialaccount__user__finished_task_states', 'socialaccount__user__finished_task_states (ManyToOneRel)'),
    ('socialaccount__user__emailaddress', 'socialaccount__user__emailaddress (ManyToOneRel)'),
    ('socialaccount__user__socialaccount', 'socialaccount__user__socialaccount (ManyToOneRel)'),
    ('socialaccount__user__media', 'socialaccount__user__media (ManyToOneRel)'),
    ('socialaccount__user__sent_drips', 'socialaccount__user__sent_drips (ManyToOneRel)'),
    ('socialaccount__user__djstripe_customers', 'socialaccount__user__djstripe_customers (ManyToOneRel)'),
    ('socialaccount__user__reactions', 'socialaccount__user__reactions (ManyToOneRel)'),
    ('socialaccount__user__flags_moderated', 'socialaccount__user__flags_moderated (ManyToOneRel)'),
    ('socialaccount__user__flags', 'socialaccount__user__flags (ManyToOneRel)'),
    ('socialaccount__user__blockeduser', 'socialaccount__user__blockeduser (ManyToOneRel)'),
    ('socialaccount__user__blockeduserhistory', 'socialaccount__user__blockeduserhistory (ManyToOneRel)'),
    ('socialaccount__user__logentry', 'socialaccount__user__logentry (ManyToOneRel)'),
    ('socialaccount__user__totpdevice', 'socialaccount__user__totpdevice (ManyToOneRel)'),
    ('socialaccount__user__staticdevice', 'socialaccount__user__staticdevice (ManyToOneRel)'),
    ('djstripe_customers', 'djstripe_customers (ManyToOneRel)'),
    ('djstripe_customers__user__id', 'djstripe_customers__user__id (AutoField)'),
    ('djstripe_customers__user__password', 'djstripe_customers__user__password (CharField)'),
    ('djstripe_customers__user__last_login', 'djstripe_customers__user__last_login (DateTimeField)'),
    ('djstripe_customers__user__is_superuser', 'djstripe_customers__user__is_superuser (BooleanField)'),
    ('djstripe_customers__user__first_name', 'djstripe_customers__user__first_name (CharField)'),
    ('djstripe_customers__user__last_name', 'djstripe_customers__user__last_name (CharField)'),
    ('djstripe_customers__user__is_staff', 'djstripe_customers__user__is_staff (BooleanField)'),
    ('djstripe_customers__user__is_active', 'djstripe_customers__user__is_active (BooleanField)'),
    ('djstripe_customers__user__date_joined', 'djstripe_customers__user__date_joined (DateTimeField)'),
    ('djstripe_customers__user__user_name', 'djstripe_customers__user__user_name (CharField)'),
    ('djstripe_customers__user__email', 'djstripe_customers__user__email (EmailField)'),
    ('djstripe_customers__user__is_mailsubscribed', 'djstripe_customers__user__is_mailsubscribed (BooleanField)'),
    ('djstripe_customers__user__is_paysubscribed', 'djstripe_customers__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('djstripe_customers__user__paysubscribe_changed', 'djstripe_customers__user__paysubscribe_changed (DateTimeField)'),
    ('djstripe_customers__user__is_smssubscribed', 'djstripe_customers__user__is_smssubscribed (BooleanField)'),
    ('djstripe_customers__user__is_newuserprofile', 'djstripe_customers__user__is_newuserprofile (BooleanField)'),
    ('djstripe_customers__user__stripe_customer', 'djstripe_customers__user__stripe_customer (ForeignKey)'),
    ('djstripe_customers__user__stripe_subscription', 'djstripe_customers__user__stripe_subscription (ForeignKey)'),
    ('djstripe_customers__user__stripe_paymentmethod', 'djstripe_customers__user__stripe_paymentmethod (ForeignKey)'),
    ('djstripe_customers__user__uuid', 'djstripe_customers__user__uuid (UUIDField)'),
    ('djstripe_customers__user__groups', 'djstripe_customers__user__groups (ManyToManyField)'),
    ('djstripe_customers__user__base_userprofile', 'djstripe_customers__user__base_userprofile (OneToOneRel)'),
    ('djstripe_customers__user__custommedia', 'djstripe_customers__user__custommedia (ManyToOneRel)'),
    ('djstripe_customers__user__podcastcontentindexpage', 'djstripe_customers__user__podcastcontentindexpage (ManyToOneRel)'),
    ('djstripe_customers__user__segment', 'djstripe_customers__user__segment (ManyToManyRel)'),
    ('djstripe_customers__user__excluded_segments', 'djstripe_customers__user__excluded_segments (ManyToManyRel)'),
    ('djstripe_customers__user__wagtail_userprofile', 'djstripe_customers__user__wagtail_userprofile (OneToOneRel)'),
    ('djstripe_customers__user__document', 'djstripe_customers__user__document (ManyToOneRel)'),
    ('djstripe_customers__user__uploadeddocument', 'djstripe_customers__user__uploadeddocument (ManyToOneRel)'),
    ('djstripe_customers__user__image', 'djstripe_customers__user__image (ManyToOneRel)'),
    ('djstripe_customers__user__uploadedimage', 'djstripe_customers__user__uploadedimage (ManyToOneRel)'),
    ('djstripe_customers__user__owned_pages', 'djstripe_customers__user__owned_pages (ManyToOneRel)'),
    ('djstripe_customers__user__locked_pages', 'djstripe_customers__user__locked_pages (ManyToOneRel)'),
    ('djstripe_customers__user__pagerevision', 'djstripe_customers__user__pagerevision (ManyToOneRel)'),
    ('djstripe_customers__user__requested_workflows', 'djstripe_customers__user__requested_workflows (ManyToOneRel)'),
    ('djstripe_customers__user__finished_task_states', 'djstripe_customers__user__finished_task_states (ManyToOneRel)'),
    ('djstripe_customers__user__emailaddress', 'djstripe_customers__user__emailaddress (ManyToOneRel)'),
    ('djstripe_customers__user__socialaccount', 'djstripe_customers__user__socialaccount (ManyToOneRel)'),
    ('djstripe_customers__user__media', 'djstripe_customers__user__media (ManyToOneRel)'),
    ('djstripe_customers__user__sent_drips', 'djstripe_customers__user__sent_drips (ManyToOneRel)'),
    ('djstripe_customers__user__djstripe_customers', 'djstripe_customers__user__djstripe_customers (ManyToOneRel)'),
    ('djstripe_customers__user__reactions', 'djstripe_customers__user__reactions (ManyToOneRel)'),
    ('djstripe_customers__user__flags_moderated', 'djstripe_customers__user__flags_moderated (ManyToOneRel)'),
    ('djstripe_customers__user__flags', 'djstripe_customers__user__flags (ManyToOneRel)'),
    ('djstripe_customers__user__blockeduser', 'djstripe_customers__user__blockeduser (ManyToOneRel)'),
    ('djstripe_customers__user__blockeduserhistory', 'djstripe_customers__user__blockeduserhistory (ManyToOneRel)'),
    ('djstripe_customers__user__logentry', 'djstripe_customers__user__logentry (ManyToOneRel)'),
    ('djstripe_customers__user__totpdevice', 'djstripe_customers__user__totpdevice (ManyToOneRel)'),
    ('djstripe_customers__user__staticdevice', 'djstripe_customers__user__staticdevice (ManyToOneRel)'),
    ('reactions', 'reactions (ManyToOneRel)'),
    ('reactions__user__id', 'reactions__user__id (AutoField)'),
    ('reactions__user__password', 'reactions__user__password (CharField)'),
    ('reactions__user__last_login', 'reactions__user__last_login (DateTimeField)'),
    ('reactions__user__is_superuser', 'reactions__user__is_superuser (BooleanField)'),
    ('reactions__user__first_name', 'reactions__user__first_name (CharField)'),
    ('reactions__user__last_name', 'reactions__user__last_name (CharField)'),
    ('reactions__user__is_staff', 'reactions__user__is_staff (BooleanField)'),
    ('reactions__user__is_active', 'reactions__user__is_active (BooleanField)'),
    ('reactions__user__date_joined', 'reactions__user__date_joined (DateTimeField)'),
    ('reactions__user__user_name', 'reactions__user__user_name (CharField)'),
    ('reactions__user__email', 'reactions__user__email (EmailField)'),
    ('reactions__user__is_mailsubscribed', 'reactions__user__is_mailsubscribed (BooleanField)'),
    ('reactions__user__is_paysubscribed', 'reactions__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('reactions__user__paysubscribe_changed', 'reactions__user__paysubscribe_changed (DateTimeField)'),
    ('reactions__user__is_smssubscribed', 'reactions__user__is_smssubscribed (BooleanField)'),
    ('reactions__user__is_newuserprofile', 'reactions__user__is_newuserprofile (BooleanField)'),
    ('reactions__user__stripe_customer', 'reactions__user__stripe_customer (ForeignKey)'),
    ('reactions__user__stripe_subscription', 'reactions__user__stripe_subscription (ForeignKey)'),
    ('reactions__user__stripe_paymentmethod', 'reactions__user__stripe_paymentmethod (ForeignKey)'),
    ('reactions__user__uuid', 'reactions__user__uuid (UUIDField)'),
    ('reactions__user__groups', 'reactions__user__groups (ManyToManyField)'),
    ('reactions__user__base_userprofile', 'reactions__user__base_userprofile (OneToOneRel)'),
    ('reactions__user__custommedia', 'reactions__user__custommedia (ManyToOneRel)'),
    ('reactions__user__podcastcontentindexpage', 'reactions__user__podcastcontentindexpage (ManyToOneRel)'),
    ('reactions__user__segment', 'reactions__user__segment (ManyToManyRel)'),
    ('reactions__user__excluded_segments', 'reactions__user__excluded_segments (ManyToManyRel)'),
    ('reactions__user__wagtail_userprofile', 'reactions__user__wagtail_userprofile (OneToOneRel)'),
    ('reactions__user__document', 'reactions__user__document (ManyToOneRel)'),
    ('reactions__user__uploadeddocument', 'reactions__user__uploadeddocument (ManyToOneRel)'),
    ('reactions__user__image', 'reactions__user__image (ManyToOneRel)'),
    ('reactions__user__uploadedimage', 'reactions__user__uploadedimage (ManyToOneRel)'),
    ('reactions__user__owned_pages', 'reactions__user__owned_pages (ManyToOneRel)'),
    ('reactions__user__locked_pages', 'reactions__user__locked_pages (ManyToOneRel)'),
    ('reactions__user__pagerevision', 'reactions__user__pagerevision (ManyToOneRel)'),
    ('reactions__user__requested_workflows', 'reactions__user__requested_workflows (ManyToOneRel)'),
    ('reactions__user__finished_task_states', 'reactions__user__finished_task_states (ManyToOneRel)'),
    ('reactions__user__emailaddress', 'reactions__user__emailaddress (ManyToOneRel)'),
    ('reactions__user__socialaccount', 'reactions__user__socialaccount (ManyToOneRel)'),
    ('reactions__user__media', 'reactions__user__media (ManyToOneRel)'),
    ('reactions__user__sent_drips', 'reactions__user__sent_drips (ManyToOneRel)'),
    ('reactions__user__djstripe_customers', 'reactions__user__djstripe_customers (ManyToOneRel)'),
    ('reactions__user__reactions', 'reactions__user__reactions (ManyToOneRel)'),
    ('reactions__user__flags_moderated', 'reactions__user__flags_moderated (ManyToOneRel)'),
    ('reactions__user__flags', 'reactions__user__flags (ManyToOneRel)'),
    ('reactions__user__blockeduser', 'reactions__user__blockeduser (ManyToOneRel)'),
    ('reactions__user__blockeduserhistory', 'reactions__user__blockeduserhistory (ManyToOneRel)'),
    ('reactions__user__logentry', 'reactions__user__logentry (ManyToOneRel)'),
    ('reactions__user__totpdevice', 'reactions__user__totpdevice (ManyToOneRel)'),
    ('reactions__user__staticdevice', 'reactions__user__staticdevice (ManyToOneRel)'),
    ('flags_moderated', 'flags_moderated (ManyToOneRel)'),
    ('flags_moderated__user__id', 'flags_moderated__user__id (AutoField)'),
    ('flags_moderated__user__password', 'flags_moderated__user__password (CharField)'),
    ('flags_moderated__user__last_login', 'flags_moderated__user__last_login (DateTimeField)'),
    ('flags_moderated__user__is_superuser', 'flags_moderated__user__is_superuser (BooleanField)'),
    ('flags_moderated__user__first_name', 'flags_moderated__user__first_name (CharField)'),
    ('flags_moderated__user__last_name', 'flags_moderated__user__last_name (CharField)'),
    ('flags_moderated__user__is_staff', 'flags_moderated__user__is_staff (BooleanField)'),
    ('flags_moderated__user__is_active', 'flags_moderated__user__is_active (BooleanField)'),
    ('flags_moderated__user__date_joined', 'flags_moderated__user__date_joined (DateTimeField)'),
    ('flags_moderated__user__user_name', 'flags_moderated__user__user_name (CharField)'),
    ('flags_moderated__user__email', 'flags_moderated__user__email (EmailField)'),
    ('flags_moderated__user__is_mailsubscribed', 'flags_moderated__user__is_mailsubscribed (BooleanField)'),
    ('flags_moderated__user__is_paysubscribed', 'flags_moderated__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('flags_moderated__user__paysubscribe_changed', 'flags_moderated__user__paysubscribe_changed (DateTimeField)'),
    ('flags_moderated__user__is_smssubscribed', 'flags_moderated__user__is_smssubscribed (BooleanField)'),
    ('flags_moderated__user__is_newuserprofile', 'flags_moderated__user__is_newuserprofile (BooleanField)'),
    ('flags_moderated__user__stripe_customer', 'flags_moderated__user__stripe_customer (ForeignKey)'),
    ('flags_moderated__user__stripe_subscription', 'flags_moderated__user__stripe_subscription (ForeignKey)'),
    ('flags_moderated__user__stripe_paymentmethod', 'flags_moderated__user__stripe_paymentmethod (ForeignKey)'),
    ('flags_moderated__user__uuid', 'flags_moderated__user__uuid (UUIDField)'),
    ('flags_moderated__user__groups', 'flags_moderated__user__groups (ManyToManyField)'),
    ('flags_moderated__user__base_userprofile', 'flags_moderated__user__base_userprofile (OneToOneRel)'),
    ('flags_moderated__user__custommedia', 'flags_moderated__user__custommedia (ManyToOneRel)'),
    ('flags_moderated__user__podcastcontentindexpage', 'flags_moderated__user__podcastcontentindexpage (ManyToOneRel)'),
    ('flags_moderated__user__segment', 'flags_moderated__user__segment (ManyToManyRel)'),
    ('flags_moderated__user__excluded_segments', 'flags_moderated__user__excluded_segments (ManyToManyRel)'),
    ('flags_moderated__user__wagtail_userprofile', 'flags_moderated__user__wagtail_userprofile (OneToOneRel)'),
    ('flags_moderated__user__document', 'flags_moderated__user__document (ManyToOneRel)'),
    ('flags_moderated__user__uploadeddocument', 'flags_moderated__user__uploadeddocument (ManyToOneRel)'),
    ('flags_moderated__user__image', 'flags_moderated__user__image (ManyToOneRel)'),
    ('flags_moderated__user__uploadedimage', 'flags_moderated__user__uploadedimage (ManyToOneRel)'),
    ('flags_moderated__user__owned_pages', 'flags_moderated__user__owned_pages (ManyToOneRel)'),
    ('flags_moderated__user__locked_pages', 'flags_moderated__user__locked_pages (ManyToOneRel)'),
    ('flags_moderated__user__pagerevision', 'flags_moderated__user__pagerevision (ManyToOneRel)'),
    ('flags_moderated__user__requested_workflows', 'flags_moderated__user__requested_workflows (ManyToOneRel)'),
    ('flags_moderated__user__finished_task_states', 'flags_moderated__user__finished_task_states (ManyToOneRel)'),
    ('flags_moderated__user__emailaddress', 'flags_moderated__user__emailaddress (ManyToOneRel)'),
    ('flags_moderated__user__socialaccount', 'flags_moderated__user__socialaccount (ManyToOneRel)'),
    ('flags_moderated__user__media', 'flags_moderated__user__media (ManyToOneRel)'),
    ('flags_moderated__user__sent_drips', 'flags_moderated__user__sent_drips (ManyToOneRel)'),
    ('flags_moderated__user__djstripe_customers', 'flags_moderated__user__djstripe_customers (ManyToOneRel)'),
    ('flags_moderated__user__reactions', 'flags_moderated__user__reactions (ManyToOneRel)'),
    ('flags_moderated__user__flags_moderated', 'flags_moderated__user__flags_moderated (ManyToOneRel)'),
    ('flags_moderated__user__flags', 'flags_moderated__user__flags (ManyToOneRel)'),
    ('flags_moderated__user__blockeduser', 'flags_moderated__user__blockeduser (ManyToOneRel)'),
    ('flags_moderated__user__blockeduserhistory', 'flags_moderated__user__blockeduserhistory (ManyToOneRel)'),
    ('flags_moderated__user__logentry', 'flags_moderated__user__logentry (ManyToOneRel)'),
    ('flags_moderated__user__totpdevice', 'flags_moderated__user__totpdevice (ManyToOneRel)'),
    ('flags_moderated__user__staticdevice', 'flags_moderated__user__staticdevice (ManyToOneRel)'),
    ('flags', 'flags (ManyToOneRel)'),
    ('flags__user__id', 'flags__user__id (AutoField)'),
    ('flags__user__password', 'flags__user__password (CharField)'),
    ('flags__user__last_login', 'flags__user__last_login (DateTimeField)'),
    ('flags__user__is_superuser', 'flags__user__is_superuser (BooleanField)'),
    ('flags__user__first_name', 'flags__user__first_name (CharField)'),
    ('flags__user__last_name', 'flags__user__last_name (CharField)'),
    ('flags__user__is_staff', 'flags__user__is_staff (BooleanField)'),
    ('flags__user__is_active', 'flags__user__is_active (BooleanField)'),
    ('flags__user__date_joined', 'flags__user__date_joined (DateTimeField)'),
    ('flags__user__user_name', 'flags__user__user_name (CharField)'),
    ('flags__user__email', 'flags__user__email (EmailField)'),
    ('flags__user__is_mailsubscribed', 'flags__user__is_mailsubscribed (BooleanField)'),
    ('flags__user__is_paysubscribed', 'flags__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('flags__user__paysubscribe_changed', 'flags__user__paysubscribe_changed (DateTimeField)'),
    ('flags__user__is_smssubscribed', 'flags__user__is_smssubscribed (BooleanField)'),
    ('flags__user__is_newuserprofile', 'flags__user__is_newuserprofile (BooleanField)'),
    ('flags__user__stripe_customer', 'flags__user__stripe_customer (ForeignKey)'),
    ('flags__user__stripe_subscription', 'flags__user__stripe_subscription (ForeignKey)'),
    ('flags__user__stripe_paymentmethod', 'flags__user__stripe_paymentmethod (ForeignKey)'),
    ('flags__user__uuid', 'flags__user__uuid (UUIDField)'),
    ('flags__user__groups', 'flags__user__groups (ManyToManyField)'),
    ('flags__user__base_userprofile', 'flags__user__base_userprofile (OneToOneRel)'),
    ('flags__user__custommedia', 'flags__user__custommedia (ManyToOneRel)'),
    ('flags__user__podcastcontentindexpage', 'flags__user__podcastcontentindexpage (ManyToOneRel)'),
    ('flags__user__segment', 'flags__user__segment (ManyToManyRel)'),
    ('flags__user__excluded_segments', 'flags__user__excluded_segments (ManyToManyRel)'),
    ('flags__user__wagtail_userprofile', 'flags__user__wagtail_userprofile (OneToOneRel)'),
    ('flags__user__document', 'flags__user__document (ManyToOneRel)'),
    ('flags__user__uploadeddocument', 'flags__user__uploadeddocument (ManyToOneRel)'),
    ('flags__user__image', 'flags__user__image (ManyToOneRel)'),
    ('flags__user__uploadedimage', 'flags__user__uploadedimage (ManyToOneRel)'),
    ('flags__user__owned_pages', 'flags__user__owned_pages (ManyToOneRel)'),
    ('flags__user__locked_pages', 'flags__user__locked_pages (ManyToOneRel)'),
    ('flags__user__pagerevision', 'flags__user__pagerevision (ManyToOneRel)'),
    ('flags__user__requested_workflows', 'flags__user__requested_workflows (ManyToOneRel)'),
    ('flags__user__finished_task_states', 'flags__user__finished_task_states (ManyToOneRel)'),
    ('flags__user__emailaddress', 'flags__user__emailaddress (ManyToOneRel)'),
    ('flags__user__socialaccount', 'flags__user__socialaccount (ManyToOneRel)'),
    ('flags__user__media', 'flags__user__media (ManyToOneRel)'),
    ('flags__user__sent_drips', 'flags__user__sent_drips (ManyToOneRel)'),
    ('flags__user__djstripe_customers', 'flags__user__djstripe_customers (ManyToOneRel)'),
    ('flags__user__reactions', 'flags__user__reactions (ManyToOneRel)'),
    ('flags__user__flags_moderated', 'flags__user__flags_moderated (ManyToOneRel)'),
    ('flags__user__flags', 'flags__user__flags (ManyToOneRel)'),
    ('flags__user__blockeduser', 'flags__user__blockeduser (ManyToOneRel)'),
    ('flags__user__blockeduserhistory', 'flags__user__blockeduserhistory (ManyToOneRel)'),
    ('flags__user__logentry', 'flags__user__logentry (ManyToOneRel)'),
    ('flags__user__totpdevice', 'flags__user__totpdevice (ManyToOneRel)'),
    ('flags__user__staticdevice', 'flags__user__staticdevice (ManyToOneRel)'),
    ('blockeduser', 'blockeduser (ManyToOneRel)'),
    ('blockeduser__user__id', 'blockeduser__user__id (AutoField)'),
    ('blockeduser__user__password', 'blockeduser__user__password (CharField)'),
    ('blockeduser__user__last_login', 'blockeduser__user__last_login (DateTimeField)'),
    ('blockeduser__user__is_superuser', 'blockeduser__user__is_superuser (BooleanField)'),
    ('blockeduser__user__first_name', 'blockeduser__user__first_name (CharField)'),
    ('blockeduser__user__last_name', 'blockeduser__user__last_name (CharField)'),
    ('blockeduser__user__is_staff', 'blockeduser__user__is_staff (BooleanField)'),
    ('blockeduser__user__is_active', 'blockeduser__user__is_active (BooleanField)'),
    ('blockeduser__user__date_joined', 'blockeduser__user__date_joined (DateTimeField)'),
    ('blockeduser__user__user_name', 'blockeduser__user__user_name (CharField)'),
    ('blockeduser__user__email', 'blockeduser__user__email (EmailField)'),
    ('blockeduser__user__is_mailsubscribed', 'blockeduser__user__is_mailsubscribed (BooleanField)'),
    ('blockeduser__user__is_paysubscribed', 'blockeduser__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('blockeduser__user__paysubscribe_changed', 'blockeduser__user__paysubscribe_changed (DateTimeField)'),
    ('blockeduser__user__is_smssubscribed', 'blockeduser__user__is_smssubscribed (BooleanField)'),
    ('blockeduser__user__is_newuserprofile', 'blockeduser__user__is_newuserprofile (BooleanField)'),
    ('blockeduser__user__stripe_customer', 'blockeduser__user__stripe_customer (ForeignKey)'),
    ('blockeduser__user__stripe_subscription', 'blockeduser__user__stripe_subscription (ForeignKey)'),
    ('blockeduser__user__stripe_paymentmethod', 'blockeduser__user__stripe_paymentmethod (ForeignKey)'),
    ('blockeduser__user__uuid', 'blockeduser__user__uuid (UUIDField)'),
    ('blockeduser__user__groups', 'blockeduser__user__groups (ManyToManyField)'),
    ('blockeduser__user__base_userprofile', 'blockeduser__user__base_userprofile (OneToOneRel)'),
    ('blockeduser__user__custommedia', 'blockeduser__user__custommedia (ManyToOneRel)'),
    ('blockeduser__user__podcastcontentindexpage', 'blockeduser__user__podcastcontentindexpage (ManyToOneRel)'),
    ('blockeduser__user__segment', 'blockeduser__user__segment (ManyToManyRel)'),
    ('blockeduser__user__excluded_segments', 'blockeduser__user__excluded_segments (ManyToManyRel)'),
    ('blockeduser__user__wagtail_userprofile', 'blockeduser__user__wagtail_userprofile (OneToOneRel)'),
    ('blockeduser__user__document', 'blockeduser__user__document (ManyToOneRel)'),
    ('blockeduser__user__uploadeddocument', 'blockeduser__user__uploadeddocument (ManyToOneRel)'),
    ('blockeduser__user__image', 'blockeduser__user__image (ManyToOneRel)'),
    ('blockeduser__user__uploadedimage', 'blockeduser__user__uploadedimage (ManyToOneRel)'),
    ('blockeduser__user__owned_pages', 'blockeduser__user__owned_pages (ManyToOneRel)'),
    ('blockeduser__user__locked_pages', 'blockeduser__user__locked_pages (ManyToOneRel)'),
    ('blockeduser__user__pagerevision', 'blockeduser__user__pagerevision (ManyToOneRel)'),
    ('blockeduser__user__requested_workflows', 'blockeduser__user__requested_workflows (ManyToOneRel)'),
    ('blockeduser__user__finished_task_states', 'blockeduser__user__finished_task_states (ManyToOneRel)'),
    ('blockeduser__user__emailaddress', 'blockeduser__user__emailaddress (ManyToOneRel)'),
    ('blockeduser__user__socialaccount', 'blockeduser__user__socialaccount (ManyToOneRel)'),
    ('blockeduser__user__media', 'blockeduser__user__media (ManyToOneRel)'),
    ('blockeduser__user__sent_drips', 'blockeduser__user__sent_drips (ManyToOneRel)'),
    ('blockeduser__user__djstripe_customers', 'blockeduser__user__djstripe_customers (ManyToOneRel)'),
    ('blockeduser__user__reactions', 'blockeduser__user__reactions (ManyToOneRel)'),
    ('blockeduser__user__flags_moderated', 'blockeduser__user__flags_moderated (ManyToOneRel)'),
    ('blockeduser__user__flags', 'blockeduser__user__flags (ManyToOneRel)'),
    ('blockeduser__user__blockeduser', 'blockeduser__user__blockeduser (ManyToOneRel)'),
    ('blockeduser__user__blockeduserhistory', 'blockeduser__user__blockeduserhistory (ManyToOneRel)'),
    ('blockeduser__user__logentry', 'blockeduser__user__logentry (ManyToOneRel)'),
    ('blockeduser__user__totpdevice', 'blockeduser__user__totpdevice (ManyToOneRel)'),
    ('blockeduser__user__staticdevice', 'blockeduser__user__staticdevice (ManyToOneRel)'),
    ('blockeduserhistory', 'blockeduserhistory (ManyToOneRel)'),
    ('blockeduserhistory__user__id', 'blockeduserhistory__user__id (AutoField)'),
    ('blockeduserhistory__user__password', 'blockeduserhistory__user__password (CharField)'),
    ('blockeduserhistory__user__last_login', 'blockeduserhistory__user__last_login (DateTimeField)'),
    ('blockeduserhistory__user__is_superuser', 'blockeduserhistory__user__is_superuser (BooleanField)'),
    ('blockeduserhistory__user__first_name', 'blockeduserhistory__user__first_name (CharField)'),
    ('blockeduserhistory__user__last_name', 'blockeduserhistory__user__last_name (CharField)'),
    ('blockeduserhistory__user__is_staff', 'blockeduserhistory__user__is_staff (BooleanField)'),
    ('blockeduserhistory__user__is_active', 'blockeduserhistory__user__is_active (BooleanField)'),
    ('blockeduserhistory__user__date_joined', 'blockeduserhistory__user__date_joined (DateTimeField)'),
    ('blockeduserhistory__user__user_name', 'blockeduserhistory__user__user_name (CharField)'),
    ('blockeduserhistory__user__email', 'blockeduserhistory__user__email (EmailField)'),
    ('blockeduserhistory__user__is_mailsubscribed', 'blockeduserhistory__user__is_mailsubscribed (BooleanField)'),
    ('blockeduserhistory__user__is_paysubscribed', 'blockeduserhistory__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('blockeduserhistory__user__paysubscribe_changed', 'blockeduserhistory__user__paysubscribe_changed (DateTimeField)'),
    ('blockeduserhistory__user__is_smssubscribed', 'blockeduserhistory__user__is_smssubscribed (BooleanField)'),
    ('blockeduserhistory__user__is_newuserprofile', 'blockeduserhistory__user__is_newuserprofile (BooleanField)'),
    ('blockeduserhistory__user__stripe_customer', 'blockeduserhistory__user__stripe_customer (ForeignKey)'),
    ('blockeduserhistory__user__stripe_subscription', 'blockeduserhistory__user__stripe_subscription (ForeignKey)'),
    ('blockeduserhistory__user__stripe_paymentmethod', 'blockeduserhistory__user__stripe_paymentmethod (ForeignKey)'),
    ('blockeduserhistory__user__uuid', 'blockeduserhistory__user__uuid (UUIDField)'),
    ('blockeduserhistory__user__groups', 'blockeduserhistory__user__groups (ManyToManyField)'),
    ('blockeduserhistory__user__base_userprofile', 'blockeduserhistory__user__base_userprofile (OneToOneRel)'),
    ('blockeduserhistory__user__custommedia', 'blockeduserhistory__user__custommedia (ManyToOneRel)'),
    ('blockeduserhistory__user__podcastcontentindexpage', 'blockeduserhistory__user__podcastcontentindexpage (ManyToOneRel)'),
    ('blockeduserhistory__user__segment', 'blockeduserhistory__user__segment (ManyToManyRel)'),
    ('blockeduserhistory__user__excluded_segments', 'blockeduserhistory__user__excluded_segments (ManyToManyRel)'),
    ('blockeduserhistory__user__wagtail_userprofile', 'blockeduserhistory__user__wagtail_userprofile (OneToOneRel)'),
    ('blockeduserhistory__user__document', 'blockeduserhistory__user__document (ManyToOneRel)'),
    ('blockeduserhistory__user__uploadeddocument', 'blockeduserhistory__user__uploadeddocument (ManyToOneRel)'),
    ('blockeduserhistory__user__image', 'blockeduserhistory__user__image (ManyToOneRel)'),
    ('blockeduserhistory__user__uploadedimage', 'blockeduserhistory__user__uploadedimage (ManyToOneRel)'),
    ('blockeduserhistory__user__owned_pages', 'blockeduserhistory__user__owned_pages (ManyToOneRel)'),
    ('blockeduserhistory__user__locked_pages', 'blockeduserhistory__user__locked_pages (ManyToOneRel)'),
    ('blockeduserhistory__user__pagerevision', 'blockeduserhistory__user__pagerevision (ManyToOneRel)'),
    ('blockeduserhistory__user__requested_workflows', 'blockeduserhistory__user__requested_workflows (ManyToOneRel)'),
    ('blockeduserhistory__user__finished_task_states', 'blockeduserhistory__user__finished_task_states (ManyToOneRel)'),
    ('blockeduserhistory__user__emailaddress', 'blockeduserhistory__user__emailaddress (ManyToOneRel)'),
    ('blockeduserhistory__user__socialaccount', 'blockeduserhistory__user__socialaccount (ManyToOneRel)'),
    ('blockeduserhistory__user__media', 'blockeduserhistory__user__media (ManyToOneRel)'),
    ('blockeduserhistory__user__sent_drips', 'blockeduserhistory__user__sent_drips (ManyToOneRel)'),
    ('blockeduserhistory__user__djstripe_customers', 'blockeduserhistory__user__djstripe_customers (ManyToOneRel)'),
    ('blockeduserhistory__user__reactions', 'blockeduserhistory__user__reactions (ManyToOneRel)'),
    ('blockeduserhistory__user__flags_moderated', 'blockeduserhistory__user__flags_moderated (ManyToOneRel)'),
    ('blockeduserhistory__user__flags', 'blockeduserhistory__user__flags (ManyToOneRel)'),
    ('blockeduserhistory__user__blockeduser', 'blockeduserhistory__user__blockeduser (ManyToOneRel)'),
    ('blockeduserhistory__user__blockeduserhistory', 'blockeduserhistory__user__blockeduserhistory (ManyToOneRel)'),
    ('blockeduserhistory__user__logentry', 'blockeduserhistory__user__logentry (ManyToOneRel)'),
    ('blockeduserhistory__user__totpdevice', 'blockeduserhistory__user__totpdevice (ManyToOneRel)'),
    ('blockeduserhistory__user__staticdevice', 'blockeduserhistory__user__staticdevice (ManyToOneRel)'),
    ('totpdevice', 'totpdevice (ManyToOneRel)'),
    ('totpdevice__user__id', 'totpdevice__user__id (AutoField)'),
    ('totpdevice__user__password', 'totpdevice__user__password (CharField)'),
    ('totpdevice__user__last_login', 'totpdevice__user__last_login (DateTimeField)'),
    ('totpdevice__user__is_superuser', 'totpdevice__user__is_superuser (BooleanField)'),
    ('totpdevice__user__first_name', 'totpdevice__user__first_name (CharField)'),
    ('totpdevice__user__last_name', 'totpdevice__user__last_name (CharField)'),
    ('totpdevice__user__is_staff', 'totpdevice__user__is_staff (BooleanField)'),
    ('totpdevice__user__is_active', 'totpdevice__user__is_active (BooleanField)'),
    ('totpdevice__user__date_joined', 'totpdevice__user__date_joined (DateTimeField)'),
    ('totpdevice__user__user_name', 'totpdevice__user__user_name (CharField)'),
    ('totpdevice__user__email', 'totpdevice__user__email (EmailField)'),
    ('totpdevice__user__is_mailsubscribed', 'totpdevice__user__is_mailsubscribed (BooleanField)'),
    ('totpdevice__user__is_paysubscribed', 'totpdevice__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('totpdevice__user__paysubscribe_changed', 'totpdevice__user__paysubscribe_changed (DateTimeField)'),
    ('totpdevice__user__is_smssubscribed', 'totpdevice__user__is_smssubscribed (BooleanField)'),
    ('totpdevice__user__is_newuserprofile', 'totpdevice__user__is_newuserprofile (BooleanField)'),
    ('totpdevice__user__stripe_customer', 'totpdevice__user__stripe_customer (ForeignKey)'),
    ('totpdevice__user__stripe_subscription', 'totpdevice__user__stripe_subscription (ForeignKey)'),
    ('totpdevice__user__stripe_paymentmethod', 'totpdevice__user__stripe_paymentmethod (ForeignKey)'),
    ('totpdevice__user__uuid', 'totpdevice__user__uuid (UUIDField)'),
    ('totpdevice__user__groups', 'totpdevice__user__groups (ManyToManyField)'),
    ('totpdevice__user__base_userprofile', 'totpdevice__user__base_userprofile (OneToOneRel)'),
    ('totpdevice__user__custommedia', 'totpdevice__user__custommedia (ManyToOneRel)'),
    ('totpdevice__user__podcastcontentindexpage', 'totpdevice__user__podcastcontentindexpage (ManyToOneRel)'),
    ('totpdevice__user__segment', 'totpdevice__user__segment (ManyToManyRel)'),
    ('totpdevice__user__excluded_segments', 'totpdevice__user__excluded_segments (ManyToManyRel)'),
    ('totpdevice__user__wagtail_userprofile', 'totpdevice__user__wagtail_userprofile (OneToOneRel)'),
    ('totpdevice__user__document', 'totpdevice__user__document (ManyToOneRel)'),
    ('totpdevice__user__uploadeddocument', 'totpdevice__user__uploadeddocument (ManyToOneRel)'),
    ('totpdevice__user__image', 'totpdevice__user__image (ManyToOneRel)'),
    ('totpdevice__user__uploadedimage', 'totpdevice__user__uploadedimage (ManyToOneRel)'),
    ('totpdevice__user__owned_pages', 'totpdevice__user__owned_pages (ManyToOneRel)'),
    ('totpdevice__user__locked_pages', 'totpdevice__user__locked_pages (ManyToOneRel)'),
    ('totpdevice__user__pagerevision', 'totpdevice__user__pagerevision (ManyToOneRel)'),
    ('totpdevice__user__requested_workflows', 'totpdevice__user__requested_workflows (ManyToOneRel)'),
    ('totpdevice__user__finished_task_states', 'totpdevice__user__finished_task_states (ManyToOneRel)'),
    ('totpdevice__user__emailaddress', 'totpdevice__user__emailaddress (ManyToOneRel)'),
    ('totpdevice__user__socialaccount', 'totpdevice__user__socialaccount (ManyToOneRel)'),
    ('totpdevice__user__media', 'totpdevice__user__media (ManyToOneRel)'),
    ('totpdevice__user__sent_drips', 'totpdevice__user__sent_drips (ManyToOneRel)'),
    ('totpdevice__user__djstripe_customers', 'totpdevice__user__djstripe_customers (ManyToOneRel)'),
    ('totpdevice__user__reactions', 'totpdevice__user__reactions (ManyToOneRel)'),
    ('totpdevice__user__flags_moderated', 'totpdevice__user__flags_moderated (ManyToOneRel)'),
    ('totpdevice__user__flags', 'totpdevice__user__flags (ManyToOneRel)'),
    ('totpdevice__user__blockeduser', 'totpdevice__user__blockeduser (ManyToOneRel)'),
    ('totpdevice__user__blockeduserhistory', 'totpdevice__user__blockeduserhistory (ManyToOneRel)'),
    ('totpdevice__user__logentry', 'totpdevice__user__logentry (ManyToOneRel)'),
    ('totpdevice__user__totpdevice', 'totpdevice__user__totpdevice (ManyToOneRel)'),
    ('totpdevice__user__staticdevice', 'totpdevice__user__staticdevice (ManyToOneRel)'),
    ('staticdevice', 'staticdevice (ManyToOneRel)'),
    ('staticdevice__user__id', 'staticdevice__user__id (AutoField)'),
    ('staticdevice__user__password', 'staticdevice__user__password (CharField)'),
    ('staticdevice__user__last_login', 'staticdevice__user__last_login (DateTimeField)'),
    ('staticdevice__user__is_superuser', 'staticdevice__user__is_superuser (BooleanField)'),
    ('staticdevice__user__first_name', 'staticdevice__user__first_name (CharField)'),
    ('staticdevice__user__last_name', 'staticdevice__user__last_name (CharField)'),
    ('staticdevice__user__is_staff', 'staticdevice__user__is_staff (BooleanField)'),
    ('staticdevice__user__is_active', 'staticdevice__user__is_active (BooleanField)'),
    ('staticdevice__user__date_joined', 'staticdevice__user__date_joined (DateTimeField)'),
    ('staticdevice__user__user_name', 'staticdevice__user__user_name (CharField)'),
    ('staticdevice__user__email', 'staticdevice__user__email (EmailField)'),
    ('staticdevice__user__is_mailsubscribed', 'staticdevice__user__is_mailsubscribed (BooleanField)'),
    ('staticdevice__user__is_paysubscribed', 'staticdevice__user__is_paysubscribed (PositiveSmallIntegerField)'),
    ('staticdevice__user__paysubscribe_changed', 'staticdevice__user__paysubscribe_changed (DateTimeField)'),
    ('staticdevice__user__is_smssubscribed', 'staticdevice__user__is_smssubscribed (BooleanField)'),
    ('staticdevice__user__is_newuserprofile', 'staticdevice__user__is_newuserprofile (BooleanField)'),
    ('staticdevice__user__stripe_customer', 'staticdevice__user__stripe_customer (ForeignKey)'),
    ('staticdevice__user__stripe_subscription', 'staticdevice__user__stripe_subscription (ForeignKey)'),
    ('staticdevice__user__stripe_paymentmethod', 'staticdevice__user__stripe_paymentmethod (ForeignKey)'),
    ('staticdevice__user__uuid', 'staticdevice__user__uuid (UUIDField)'),
    ('staticdevice__user__groups', 'staticdevice__user__groups (ManyToManyField)'),
    ('staticdevice__user__base_userprofile', 'staticdevice__user__base_userprofile (OneToOneRel)'),
    ('staticdevice__user__custommedia', 'staticdevice__user__custommedia (ManyToOneRel)'),
    ('staticdevice__user__podcastcontentindexpage', 'staticdevice__user__podcastcontentindexpage (ManyToOneRel)'),
    ('staticdevice__user__segment', 'staticdevice__user__segment (ManyToManyRel)'),
    ('staticdevice__user__excluded_segments', 'staticdevice__user__excluded_segments (ManyToManyRel)'),
    ('staticdevice__user__wagtail_userprofile', 'staticdevice__user__wagtail_userprofile (OneToOneRel)'),
    ('staticdevice__user__document', 'staticdevice__user__document (ManyToOneRel)'),
    ('staticdevice__user__uploadeddocument', 'staticdevice__user__uploadeddocument (ManyToOneRel)'),
    ('staticdevice__user__image', 'staticdevice__user__image (ManyToOneRel)'),
    ('staticdevice__user__uploadedimage', 'staticdevice__user__uploadedimage (ManyToOneRel)'),
    ('staticdevice__user__owned_pages', 'staticdevice__user__owned_pages (ManyToOneRel)'),
    ('staticdevice__user__locked_pages', 'staticdevice__user__locked_pages (ManyToOneRel)'),
    ('staticdevice__user__pagerevision', 'staticdevice__user__pagerevision (ManyToOneRel)'),
    ('staticdevice__user__requested_workflows', 'staticdevice__user__requested_workflows (ManyToOneRel)'),
    ('staticdevice__user__finished_task_states', 'staticdevice__user__finished_task_states (ManyToOneRel)'),
    ('staticdevice__user__emailaddress', 'staticdevice__user__emailaddress (ManyToOneRel)'),
    ('staticdevice__user__socialaccount', 'staticdevice__user__socialaccount (ManyToOneRel)'),
    ('staticdevice__user__media', 'staticdevice__user__media (ManyToOneRel)'),
    ('staticdevice__user__sent_drips', 'staticdevice__user__sent_drips (ManyToOneRel)'),
    ('staticdevice__user__djstripe_customers', 'staticdevice__user__djstripe_customers (ManyToOneRel)'),
    ('staticdevice__user__reactions', 'staticdevice__user__reactions (ManyToOneRel)'),
    ('staticdevice__user__flags_moderated', 'staticdevice__user__flags_moderated (ManyToOneRel)'),
    ('staticdevice__user__flags', 'staticdevice__user__flags (ManyToOneRel)'),
    ('staticdevice__user__blockeduser', 'staticdevice__user__blockeduser (ManyToOneRel)'),
    ('staticdevice__user__blockeduserhistory', 'staticdevice__user__blockeduserhistory (ManyToOneRel)'),
    ('staticdevice__user__logentry', 'staticdevice__user__logentry (ManyToOneRel)'),
    ('staticdevice__user__totpdevice', 'staticdevice__user__totpdevice (ManyToOneRel)'),
    ('staticdevice__user__staticdevice', 'staticdevice__user__staticdevice (ManyToOneRel)'),
)

RULE_TYPES = (
    ('or', 'Or'),
    ('and', 'And'),
)


class AbstractQuerySetRule(models.Model):
    """
    Allows to apply filters to drips
    """
    date = models.DateTimeField(auto_now_add=True)
    lastchanged = models.DateTimeField(auto_now=True)

    drip = models.ForeignKey(
        Drip,
        related_name='queryset_rules',
        on_delete=models.CASCADE,
    )

    method_type = models.CharField(
        max_length=12,
        default='filter',
        choices=METHOD_TYPES,
    )
    field_name = models.CharField(
        max_length=128, verbose_name='Field name of User'
    )
    lookup_type = models.CharField(
        max_length=12, default='exact', choices=LOOKUP_TYPES
    )
    rule_type = models.CharField(
        max_length=3, default='and', choices=RULE_TYPES
    )

    field_value = models.CharField(
        max_length=255,
        help_text=(
            'Can be anything from a number, to a string. Or, do ' +
            '`now-7 days` or `today+3 days` for fancy timedelta.'
        )
    )

    def clean(self) -> None:
        User = get_user_model()
        try:
            self.apply(User.objects.all())
        except Exception as e:
            raise ValidationError(
                '{type_name} raised trying to apply rule: {error}'.format(
                    type_name=type(e).__name__,
                    error=str(e),
                )
            )

    @property
    def annotated_field_name(self) -> str:
        """
        Generates an annotated version of this field's name,
        based on self.field_name
        """
        field_name = self.field_name
        if field_name.endswith('__count'):
            agg, _, _ = field_name.rpartition('__')
            field_name = 'num_{agg}'.format(agg=agg.replace('__', '_'))

        return field_name

    def apply_any_annotation(self, qs: AbstractQuerySetRuleQuerySet) -> AbstractQuerySetRuleQuerySet:  # noqa: E501
        """
        Returns qs annotated with Count over this field's name.
        """
        if self.field_name.endswith('__count'):
            field_name = self.annotated_field_name
            agg, _, _ = self.field_name.rpartition('__')
            qs = qs.annotate(**{field_name: models.Count(agg, distinct=True)})
        return qs

    def set_time_deltas_and_dates(self, now: DateTime, field_value: str) -> TimeDeltaOrStr:  # noqa: E501
        """
        Parses the field_value parameter and returns a TimeDelta object
        The field_value string might start with one of
        the following substrings:
        * "now-"
        * "now+"
        * "today-"
        * "today+"
        Otherwise returns field_value unchanged.
        """
        # set time deltas and dates
        if self.field_value.startswith('now-'):
            field_value = self.field_value.replace('now-', '')
            field_value = now() - parse(field_value)
        elif self.field_value.startswith('now+'):
            field_value = self.field_value.replace('now+', '')
            field_value = now() + parse(field_value)
        elif self.field_value.startswith('today-'):
            field_value = self.field_value.replace('today-', '')
            field_value = now().date() - parse(field_value)
        elif self.field_value.startswith('today+'):
            field_value = self.field_value.replace('today+', '')
            field_value = now().date() + parse(field_value)
        return field_value

    def set_f_expressions(self, field_value: str) -> FExpressionOrStr:
        """
        If field_value starts with the substring 'F\_', returns an instance
        of models.F within the field_value expression, otherwise returns
        field_value unchanged.
        """  # noqa: W605
        # F expressions
        if self.field_value.startswith('F_'):
            field_value = self.field_value.replace('F_', '')
            field_value = models.F(field_value)
        return field_value

    def set_booleans(self, field_value: str) -> BoolOrStr:
        """
        Returns True or False whether field value is 'True' or
        'False' respectively.
        Otherwise returns field_value unchanged.
        """
        # set booleans
        if self.field_value == 'True':
            field_value = True
        if self.field_value == 'False':
            field_value = False
        return field_value

    def filter_kwargs(self, now: DateTime = datetime.now) -> dict:
        """
        Returns a dictionary {field_name: field_value} where:

        - field_name is self.annotated_field_name in addition to
          self.lookup_type in the form FIELD_NAME__LOOKUP.
        - field_value is the result of passing self.field_value
          through parsing methods.

        The resulting dict can be used to apply filters over querysets.

        .. code-block:: python

          queryset.filter(**obj.filter_kwargs(datetime.now()))

        """
        # Support Count() as m2m__count
        field_name = self.annotated_field_name
        field_name = '__'.join([field_name, self.lookup_type])
        field_value = self.field_value

        field_value = self.set_time_deltas_and_dates(now, field_value)

        field_value = self.set_f_expressions(field_value)

        field_value = self.set_booleans(field_value)

        kwargs = {field_name: field_value}

        return kwargs

    def apply(self, qs: AbstractQuerySetRuleQuerySet, now: DateTime = datetime.now) -> AbstractQuerySetRuleQuerySet:  # noqa: E501
        """
        Returns ``qs`` filtered/excluded by any filter resulting
        from ``self.filter_kwargs`` depending on whether
        ``self.method_type`` is one of the following:

        - "filter"
        - "exclude"

        Also annotates ``qs`` by calling ``self.apply_any_annotation``.
        """
        kwargs = self.filter_kwargs(now)
        qs = self.apply_any_annotation(qs)

        if self.method_type == 'filter':
            return qs.filter(**kwargs)
        elif self.method_type == 'exclude':
            return qs.exclude(**kwargs)

        # catch as default
        return qs.filter(**kwargs)

    class Meta:
        abstract = True


class QuerySetRule(AbstractQuerySetRule, Orderable):
    drip = ParentalKey(
        Drip,
        related_name='queryset_rules',
        on_delete=models.CASCADE,
    )

    method_type = models.CharField(
        max_length=100,
        default='filter',
        choices=METHOD_TYPES,
    )
    field_name = models.CharField(
        max_length=100, default='last_login', choices=FIELD_NAMES
    )
    lookup_type = models.CharField(
        max_length=100, default='exact', choices=LOOKUP_TYPES
    )
    
    panels = [
        FieldPanel('method_type'),
        FieldPanel('field_name'),
        FieldPanel('lookup_type'),
        FieldPanel('field_value'),
        FieldPanel('rule_type'),
    ]


class TestUserUUIDModel(models.Model):
    """
    Class to test UUID field as id in User model
    """
    id = models.UUIDField(primary_key=True)
