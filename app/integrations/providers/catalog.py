"""Provider catalog — registers all enterprise integration providers."""

from __future__ import annotations

from app.core.enums import (
    IntegrationAuthType,
    IntegrationCategory,
    IntegrationEntityType,
    IntegrationProviderSlug,
)
from app.integrations.providers.base import IntegrationProvider, ProviderMetadata
from app.integrations.providers.oauth_base import ApiKeyIntegrationProvider, OAuthIntegrationProvider


def _oauth_meta(
    slug: IntegrationProviderSlug,
    name: str,
    category: IntegrationCategory,
    entities: tuple[IntegrationEntityType, ...],
    *,
    authorize: str,
    token: str,
    revoke: str | None = None,
    scopes: tuple[str, ...] = (),
    webhook_header: str | None = None,
    docs: str | None = None,
) -> ProviderMetadata:
    return ProviderMetadata(
        slug=slug,
        name=name,
        category=category,
        auth_type=IntegrationAuthType.OAUTH2,
        description=f"Connect {name} to synchronize enterprise data.",
        supported_entities=entities,
        oauth_authorize_url=authorize,
        oauth_token_url=token,
        oauth_revoke_url=revoke,
        default_scopes=scopes,
        webhook_signature_header=webhook_header,
        docs_url=docs,
    )


def _api_key_meta(
    slug: IntegrationProviderSlug,
    name: str,
    category: IntegrationCategory,
    entities: tuple[IntegrationEntityType, ...],
    *,
    webhook_header: str | None = None,
) -> ProviderMetadata:
    return ProviderMetadata(
        slug=slug,
        name=name,
        category=category,
        auth_type=IntegrationAuthType.API_KEY,
        description=f"Connect {name} via API key.",
        supported_entities=entities,
        webhook_signature_header=webhook_header,
    )


def _provider(meta: ProviderMetadata) -> IntegrationProvider:
    if meta.auth_type == IntegrationAuthType.OAUTH2:

        class Provider(OAuthIntegrationProvider):
            @property
            def metadata(self) -> ProviderMetadata:
                return meta

        return Provider()

    class Provider(ApiKeyIntegrationProvider):
        @property
        def metadata(self) -> ProviderMetadata:
            return meta

    return Provider()


def build_provider_catalog() -> list[IntegrationProvider]:
    """Build full provider catalog — plugin registration point."""
    definitions: list[ProviderMetadata] = [
        # CRM
        _oauth_meta(
            IntegrationProviderSlug.HUBSPOT,
            "HubSpot",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER),
            authorize="https://app.hubspot.com/oauth/authorize",
            token="https://api.hubapi.com/oauth/v1/token",
            scopes=("crm.objects.contacts.read", "crm.objects.deals.read"),
            webhook_header="X-HubSpot-Signature",
            docs="https://developers.hubspot.com/docs/api/overview",
        ),
        _oauth_meta(
            IntegrationProviderSlug.SALESFORCE,
            "Salesforce",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER, IntegrationEntityType.APPOINTMENT),
            authorize="https://login.salesforce.com/services/oauth2/authorize",
            token="https://login.salesforce.com/services/oauth2/token",
            revoke="https://login.salesforce.com/services/oauth2/revoke",
            scopes=("api", "refresh_token"),
            docs="https://developer.salesforce.com/docs",
        ),
        _oauth_meta(
            IntegrationProviderSlug.ZOHO_CRM,
            "Zoho CRM",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER),
            authorize="https://accounts.zoho.com/oauth/v2/auth",
            token="https://accounts.zoho.com/oauth/v2/token",
            scopes=("ZohoCRM.modules.ALL",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.MICROSOFT_DYNAMICS,
            "Microsoft Dynamics 365",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scopes=("https://org.crm.dynamics.com/.default",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.PIPEDRIVE,
            "Pipedrive",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER),
            authorize="https://oauth.pipedrive.com/oauth/authorize",
            token="https://oauth.pipedrive.com/oauth/token",
        ),
        _api_key_meta(
            IntegrationProviderSlug.FRESHSALES,
            "Freshsales",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT),
        ),
        _api_key_meta(
            IntegrationProviderSlug.CUSTOM_CRM,
            "Custom CRM API",
            IntegrationCategory.CRM,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.CONTACT, IntegrationEntityType.ORDER),
        ),
        # Helpdesk
        _oauth_meta(
            IntegrationProviderSlug.ZENDESK,
            "Zendesk",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.CUSTOMER, IntegrationEntityType.EMPLOYEE),
            authorize="https://{subdomain}.zendesk.com/oauth/authorizations/new",
            token="https://{subdomain}.zendesk.com/oauth/tokens",
            webhook_header="X-Zendesk-Webhook-Signature",
        ),
        _api_key_meta(
            IntegrationProviderSlug.FRESHDESK,
            "Freshdesk",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.CUSTOMER),
        ),
        _oauth_meta(
            IntegrationProviderSlug.INTERCOM,
            "Intercom",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.CUSTOMER),
            authorize="https://app.intercom.com/oauth",
            token="https://api.intercom.io/auth/eagle/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.SERVICENOW,
            "ServiceNow",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.EMPLOYEE, IntegrationEntityType.KNOWLEDGE),
            authorize="https://{instance}.service-now.com/oauth_auth.do",
            token="https://{instance}.service-now.com/oauth_token.do",
        ),
        _api_key_meta(
            IntegrationProviderSlug.HELP_SCOUT,
            "Help Scout",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.CUSTOMER),
        ),
        _oauth_meta(
            IntegrationProviderSlug.ZOHO_DESK,
            "Zoho Desk",
            IntegrationCategory.HELPDESK,
            (IntegrationEntityType.TICKET, IntegrationEntityType.CUSTOMER),
            authorize="https://accounts.zoho.com/oauth/v2/auth",
            token="https://accounts.zoho.com/oauth/v2/token",
        ),
        # Ecommerce
        _oauth_meta(
            IntegrationProviderSlug.SHOPIFY,
            "Shopify",
            IntegrationCategory.ECOMMERCE,
            (IntegrationEntityType.PRODUCT, IntegrationEntityType.ORDER, IntegrationEntityType.CUSTOMER),
            authorize="https://{shop}.myshopify.com/admin/oauth/authorize",
            token="https://{shop}.myshopify.com/admin/oauth/access_token",
            scopes=("read_products", "read_orders", "read_customers"),
            webhook_header="X-Shopify-Hmac-Sha256",
        ),
        _api_key_meta(
            IntegrationProviderSlug.WOOCOMMERCE,
            "WooCommerce",
            IntegrationCategory.ECOMMERCE,
            (IntegrationEntityType.PRODUCT, IntegrationEntityType.ORDER, IntegrationEntityType.CUSTOMER),
        ),
        _oauth_meta(
            IntegrationProviderSlug.MAGENTO,
            "Magento",
            IntegrationCategory.ECOMMERCE,
            (IntegrationEntityType.PRODUCT, IntegrationEntityType.ORDER, IntegrationEntityType.CUSTOMER),
            authorize="https://{store}/oauth/authorize",
            token="https://{store}/oauth/token",
        ),
        _api_key_meta(
            IntegrationProviderSlug.BIGCOMMERCE,
            "BigCommerce",
            IntegrationCategory.ECOMMERCE,
            (IntegrationEntityType.PRODUCT, IntegrationEntityType.ORDER, IntegrationEntityType.CUSTOMER),
        ),
        _api_key_meta(
            IntegrationProviderSlug.PRESTASHOP,
            "PrestaShop",
            IntegrationCategory.ECOMMERCE,
            (IntegrationEntityType.PRODUCT, IntegrationEntityType.ORDER, IntegrationEntityType.CUSTOMER),
        ),
        # Calendar
        _oauth_meta(
            IntegrationProviderSlug.GOOGLE_CALENDAR,
            "Google Calendar",
            IntegrationCategory.CALENDAR,
            (IntegrationEntityType.APPOINTMENT, IntegrationEntityType.CALENDAR_EVENT),
            authorize="https://accounts.google.com/o/oauth2/v2/auth",
            token="https://oauth2.googleapis.com/token",
            revoke="https://oauth2.googleapis.com/revoke",
            scopes=("https://www.googleapis.com/auth/calendar.readonly",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.MICROSOFT_OUTLOOK,
            "Microsoft Outlook Calendar",
            IntegrationCategory.CALENDAR,
            (IntegrationEntityType.APPOINTMENT, IntegrationEntityType.CALENDAR_EVENT),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scopes=("Calendars.Read", "offline_access"),
        ),
        _oauth_meta(
            IntegrationProviderSlug.CALENDLY,
            "Calendly",
            IntegrationCategory.CALENDAR,
            (IntegrationEntityType.APPOINTMENT, IntegrationEntityType.CALENDAR_EVENT),
            authorize="https://auth.calendly.com/oauth/authorize",
            token="https://auth.calendly.com/oauth/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.APPLE_CALENDAR,
            "Apple Calendar",
            IntegrationCategory.CALENDAR,
            (IntegrationEntityType.APPOINTMENT, IntegrationEntityType.CALENDAR_EVENT),
            authorize="https://appleid.apple.com/auth/authorize",
            token="https://appleid.apple.com/auth/token",
        ),
        # Email
        _oauth_meta(
            IntegrationProviderSlug.GMAIL,
            "Gmail",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL, IntegrationEntityType.CONTACT),
            authorize="https://accounts.google.com/o/oauth2/v2/auth",
            token="https://oauth2.googleapis.com/token",
            scopes=("https://www.googleapis.com/auth/gmail.readonly",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.MICROSOFT_365,
            "Microsoft 365",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL, IntegrationEntityType.CONTACT, IntegrationEntityType.EMPLOYEE),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scopes=("Mail.Read", "User.Read", "offline_access"),
        ),
        _api_key_meta(
            IntegrationProviderSlug.SMTP,
            "SMTP",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL,),
        ),
        _api_key_meta(
            IntegrationProviderSlug.SENDGRID,
            "SendGrid",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL,),
        ),
        _api_key_meta(
            IntegrationProviderSlug.MAILGUN,
            "Mailgun",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL,),
        ),
        _api_key_meta(
            IntegrationProviderSlug.AMAZON_SES,
            "Amazon SES",
            IntegrationCategory.EMAIL,
            (IntegrationEntityType.EMAIL,),
        ),
        # Identity
        _oauth_meta(
            IntegrationProviderSlug.MICROSOFT_ENTRA,
            "Microsoft Entra ID",
            IntegrationCategory.IDENTITY,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            scopes=("User.Read.All", "Directory.Read.All"),
        ),
        _oauth_meta(
            IntegrationProviderSlug.OKTA,
            "Okta",
            IntegrationCategory.IDENTITY,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://{domain}/oauth2/v1/authorize",
            token="https://{domain}/oauth2/v1/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.GOOGLE_WORKSPACE,
            "Google Workspace",
            IntegrationCategory.IDENTITY,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://accounts.google.com/o/oauth2/v2/auth",
            token="https://oauth2.googleapis.com/token",
            scopes=("https://www.googleapis.com/auth/admin.directory.user.readonly",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.AZURE_AD,
            "Azure AD",
            IntegrationCategory.IDENTITY,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        ),
        # Communication
        _oauth_meta(
            IntegrationProviderSlug.SLACK,
            "Slack",
            IntegrationCategory.COMMUNICATION,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://slack.com/oauth/v2/authorize",
            token="https://slack.com/api/oauth.v2.access",
            scopes=("channels:read", "users:read"),
            webhook_header="X-Slack-Signature",
        ),
        _oauth_meta(
            IntegrationProviderSlug.MICROSOFT_TEAMS,
            "Microsoft Teams",
            IntegrationCategory.COMMUNICATION,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.DISCORD,
            "Discord",
            IntegrationCategory.COMMUNICATION,
            (IntegrationEntityType.EMPLOYEE, IntegrationEntityType.CONTACT),
            authorize="https://discord.com/api/oauth2/authorize",
            token="https://discord.com/api/oauth2/token",
        ),
        _api_key_meta(
            IntegrationProviderSlug.WEBHOOK,
            "Generic Webhook",
            IntegrationCategory.COMMUNICATION,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.TICKET, IntegrationEntityType.ORDER),
        ),
        # Payment
        _api_key_meta(
            IntegrationProviderSlug.STRIPE,
            "Stripe",
            IntegrationCategory.PAYMENT,
            (IntegrationEntityType.ORDER, IntegrationEntityType.SUBSCRIPTION, IntegrationEntityType.INVOICE),
            webhook_header="Stripe-Signature",
        ),
        _oauth_meta(
            IntegrationProviderSlug.PAYPAL,
            "PayPal",
            IntegrationCategory.PAYMENT,
            (IntegrationEntityType.ORDER, IntegrationEntityType.INVOICE),
            authorize="https://www.paypal.com/signin/authorize",
            token="https://api.paypal.com/v1/oauth2/token",
        ),
        _api_key_meta(
            IntegrationProviderSlug.ADYEN,
            "Adyen",
            IntegrationCategory.PAYMENT,
            (IntegrationEntityType.ORDER, IntegrationEntityType.INVOICE),
        ),
        # Knowledge
        _oauth_meta(
            IntegrationProviderSlug.NOTION,
            "Notion",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://api.notion.com/v1/oauth/authorize",
            token="https://api.notion.com/v1/oauth/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.CONFLUENCE,
            "Confluence",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://auth.atlassian.com/authorize",
            token="https://auth.atlassian.com/oauth/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.GOOGLE_DRIVE,
            "Google Drive",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://accounts.google.com/o/oauth2/v2/auth",
            token="https://oauth2.googleapis.com/token",
            scopes=("https://www.googleapis.com/auth/drive.readonly",),
        ),
        _oauth_meta(
            IntegrationProviderSlug.SHAREPOINT,
            "SharePoint",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.DROPBOX,
            "Dropbox",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://www.dropbox.com/oauth2/authorize",
            token="https://api.dropboxapi.com/oauth2/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.ONEDRIVE,
            "OneDrive",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        ),
        _oauth_meta(
            IntegrationProviderSlug.BOX,
            "Box",
            IntegrationCategory.KNOWLEDGE,
            (IntegrationEntityType.KNOWLEDGE,),
            authorize="https://account.box.com/api/oauth2/authorize",
            token="https://api.box.com/oauth2/token",
        ),
        # Phone
        _api_key_meta(
            IntegrationProviderSlug.TWILIO,
            "Twilio",
            IntegrationCategory.PHONE,
            (IntegrationEntityType.CUSTOMER, IntegrationEntityType.APPOINTMENT),
        ),
        _api_key_meta(
            IntegrationProviderSlug.SIP,
            "SIP Trunk",
            IntegrationCategory.PHONE,
            (IntegrationEntityType.CUSTOMER,),
        ),
        _api_key_meta(
            IntegrationProviderSlug.BYOC,
            "Bring Your Own Carrier",
            IntegrationCategory.PHONE,
            (IntegrationEntityType.CUSTOMER,),
        ),
    ]
    return [_provider(d) for d in definitions]
