# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms.pool_questions import PoolQuestionsForm
from admission.contrib.forms.specific_question import ConfigurableFormMixin
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import FormMixinWithSpecificQuestions, WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['SpecificQuestionsFormView']


class SpecificQuestionsFormView(LoadDossierViewMixin, WebServiceFormMixin, FormMixinWithSpecificQuestions, FormView):
    template_name = 'admission/forms/specific_question.html'
    tab_of_specific_questions = Onglets.INFORMATIONS_ADDITIONNELLES.name
    service_mapping = {
        'general-education': AdmissionPropositionService.update_general_specific_question,
        'continuing-education': AdmissionPropositionService.update_continuing_specific_question,
    }

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms):
            self.service_mapping[self.current_context](
                person=self.person,
                uuid=self.admission_uuid,
                data=forms[0].cleaned_data,
            )
            if self.display_pool_questions_form:
                AdmissionPropositionService.update_pool_questions(
                    person=self.person,
                    uuid=self.admission_uuid,
                    data=forms[1].cleaned_data,
                )
            return HttpResponseRedirect(self.get_success_url())
        return self.form_invalid(forms)

    def call_webservice(self, data):
        # Replaced by the custom calls in post()
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        kwargs['extra_form_attrs'] = ' autocomplete="off"'
        kwargs['forms'] = self.get_forms()
        kwargs['form'] = kwargs['forms'][0]  # Trick template to display form tag and buttons
        if self.display_pool_questions_form:
            kwargs['reorientation_pool_end_date'] = self.pool_questions['reorientation_pool_end_date']
            kwargs['modification_pool_end_date'] = self.pool_questions['modification_pool_end_date']
        return super().get_context_data(**kwargs)

    def get_forms(self):
        form_kwargs = self.get_form_kwargs()
        forms = [
            ConfigurableFormMixin(
                self.request.POST or None,
                form_item_configurations=form_kwargs['form_item_configurations'],
                initial={'specific_question_answers': self.admission.reponses_questions_specifiques},
                prefix='specific_questions',
            )
        ]
        if self.display_pool_questions_form:
            forms.append(
                PoolQuestionsForm(
                    self.request.POST or None,
                    initial=self.pool_questions,
                    prefix='pool_questions',
                )
            )
        return forms

    @property
    def display_pool_questions_form(self):
        return (
            self.current_context == 'general-education'
            and self.admission.formation['type'] == TrainingType.BACHELOR.name
        )

    @cached_property
    def pool_questions(self):
        return AdmissionPropositionService.get_pool_questions(self.person, self.admission_uuid).to_dict()
