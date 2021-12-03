from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import action_links_api

from frontoffice.settings.osis_sdk import admission as admission_sdk

from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers, api_exception_handler


class ActionLinksAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return action_links_api.ActionLinksApi(ApiClient(configuration=api_config))


class ActionLinksService:

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def get_action_links(cls, person, **kwargs):
        return ActionLinksAPIClient().retrieve_action_links(**build_mandatory_auth_headers(person))
