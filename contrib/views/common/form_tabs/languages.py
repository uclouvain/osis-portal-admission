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
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import Context, Template
from django.utils.translation import get_language
from django.views.generic import FormView

from admission.contrib.forms.languages import DoctorateAdmissionLanguagesKnowledgeFormSet, MANDATORY_LANGUAGES
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from admission.services.reference import LanguageService
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException

__all__ = ['AdmissionLanguagesFormView']


class AdmissionLanguagesFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/forms/languages.html"
    form_class = DoctorateAdmissionLanguagesKnowledgeFormSet

    def get(self, request, *args, **kwargs):
        if not self.admission_uuid:
            # Trick template to not display form and buttons
            context = super(LoadDossierViewMixin, self).get_context_data(form=None, **kwargs)
            return render(request, 'admission/forms/need_training_choice.html', context)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        template_empty_form = """
            {% load bootstrap3 i18n static admission %}
            <div class="form-container">
              {% panel _("Add a language") %}
                {% bootstrap_field language_form.language %}
                {% bootstrap_field language_form.listening_comprehension %}
                {% bootstrap_field language_form.speaking_ability %}
                {% bootstrap_field language_form.writing_ability %}
                {% bootstrap_field_with_tooltip language_form.certificate %}
              {% endpanel %}
            </div>
        """
        template = Template(template_empty_form)
        context = Context({'language_form': context_data["form"].empty_form})

        context_data["empty_form"] = template.render(context)
        context_data["MANDATORY_LANGUAGES"] = MANDATORY_LANGUAGES
        context_data["languages"] = {
            lang.code: lang.name if get_language() == settings.LANGUAGE_CODE else lang.name_en
            for lang in LanguageService.get_languages(person=self.request.user.person)
        }

        # Trick template to display the form tag
        context_data["formset"] = context_data["form"]
        context_data["form"] = context_data["form"].empty_form
        return context_data

    def get_initial(self):
        return [
            language_knowledge.to_dict()
            for language_knowledge in AdmissionPersonService.retrieve_languages_knowledge(
                self.person,
                uuid=self.admission_uuid,
            )
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {"person": self.person}
        return kwargs

    def call_webservice(self, data):
        AdmissionPersonService.update_languages_knowledge(self.person, data, uuid=self.admission_uuid)

    def form_valid(self, formset):
        data = [form.cleaned_data for form in formset.forms if form not in formset.deleted_forms]

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:  # pragma: no cover
            for exception in multiple_business_api_exception.exceptions:
                if exception.status_code in self._error_mapping:
                    formset.add_error(self._error_mapping[exception.status_code], exception.detail)
                else:
                    formset.add_error(None, exception.detail)
            return self.form_invalid(formset)
        return HttpResponseRedirect(self.get_success_url())
