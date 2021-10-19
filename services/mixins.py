# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException


class WebServiceFormMixin:
    error_mapping = {}

    def __init__(self, *args, **kwargs):
        self._error_mapping = {exc.value: field for exc, field in self.error_mapping.items()}
        super().__init__(*args, **kwargs)

    def prepare_data(self, data):
        return data

    def form_valid(self, form):
        data = self.prepare_data(dict(**form.cleaned_data))

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:
            for exception in multiple_business_api_exception.exceptions:
                if exception.status_code in self._error_mapping:
                    form.add_error(self._error_mapping[exception.status_code], exception.detail)
                else:
                    form.add_error(None, exception.detail)
            return self.form_invalid(form)
        return super().form_valid(form)

    def call_webservice(self, data):
        raise NotImplementedError
