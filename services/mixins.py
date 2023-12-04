# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import re
from copy import copy

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from osis_admission_sdk import OpenApiException

from admission.contrib.enums import IN_PROGRESS_STATUSES
from base.models.person import Person
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException, api_exception_handler


INVALID_LENGTH_RE = re.compile('Invalid value for `([^`]+)`, length must be less than or equal to `([^`]+)`')


class WebServiceFormMixin:
    error_mapping = {}

    def __init__(self, *args, **kwargs):
        self._error_mapping = {exc.value: field for exc, field in self.error_mapping.items()}
        super().__init__(*args, **kwargs)

    def prepare_data(self, data):
        return data

    def form_invalid(self, form):
        # On error, display global message
        messages.error(self.request, _("Please correct the errors below"))
        return super().form_invalid(form)

    def handle_form_exception(self, form, exception):
        if exception.status_code in self._error_mapping:
            form.add_error(self._error_mapping[exception.status_code], exception.detail)
        else:
            form.add_error(None, exception.detail)

    def form_valid(self, form):
        data = self.prepare_data(copy(form.cleaned_data))

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:
            for exception in multiple_business_api_exception.exceptions:
                self.handle_form_exception(form, exception)
            return self.form_invalid(form)
        except PermissionDenied as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except OpenApiException as e:
            # We try to be smart about the error
            invalid_length = INVALID_LENGTH_RE.match(str(e))
            if invalid_length is not None and invalid_length.group(1) in form.fields:
                form.add_error(
                    invalid_length.group(1),
                    _("This field must be less that {length} characters.").format(length=invalid_length.group(2)),
                )
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_next_tab_name(self, for_context=None):
        from admission.templatetags.admission import TAB_TREES

        for_context = for_context or self.current_context

        flat_tab_list = [child.name for tab, children in TAB_TREES[for_context].items() for child in children]
        return flat_tab_list[flat_tab_list.index(self.request.resolver_match.url_name) + 1]

    def call_webservice(self, data):
        raise NotImplementedError

    def get_success_url(self):
        from admission.templatetags.admission import can_update_tab, TAB_TREES

        messages.info(self.request, _("Your data have been saved"))

        # If a url to redirect is specified in the request, use it
        if self.request.POST.get('redirect_to'):
            return self.request.POST.get('redirect_to')

        if self.success_url:
            return self.success_url

        tab_mapping = {
            child.name: child for tab, children in TAB_TREES[self.current_context].items() for child in children
        }

        if (
            # We are creating an admission, on profile tabs
            not self.kwargs.get('pk', None)
            or (
                # We are on an admission in progress, as candidate
                hasattr(self, 'admission')
                and self.admission.matricule_candidat == self.request.user.person.global_id
                and self.admission.statut in IN_PROGRESS_STATUSES
            )
        ):
            tab_to_redirect = tab_mapping[
                self.get_next_tab_name()
                # Redirect on next tab in tab list if submit_and_continue
                if '_submit_and_continue' in self.request.POST
                else self.request.resolver_match.url_name
            ]
            if not self.kwargs.get('pk', None) or can_update_tab(self.admission, tab_to_redirect):
                return self._get_url(tab_to_redirect.name, update=True)

        # Redirect on detail
        return self._get_url(self.request.resolver_match.url_name)

    @property
    def person(self) -> Person:
        return self.request.user.person


class FormMixinWithSpecificQuestions:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = (
            [configuration.to_dict() for configuration in getattr(self, 'specific_questions', [])]
            if self.kwargs.get('pk')
            else []
        )
        return kwargs


class ServiceMeta(type):
    """
    A metaclass that decorates all class methods with exception handler.

    'api_exception_cls' must be specified as attribute
    """

    def __new__(mcs, name, bases, attrs):
        if 'api_exception_cls' not in attrs:
            raise AttributeError("{name} must declare 'api_exception_cls' attribute".format(name=name))
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, classmethod):
                attrs[attr_name] = classmethod(api_exception_handler(attrs['api_exception_cls'])(attr_value.__func__))
        return super().__new__(mcs, name, bases, attrs)
