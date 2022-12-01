# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin

from admission.services.doctorate import AdmissionDoctorateService
from admission.services.proposition import AdmissionPropositionService


class LoadViewMixin(LoginRequiredMixin, ContextMixin):
    detail_base_template = ''
    form_base_template = ''

    @property
    def current_context(self):
        return self.request.resolver_match.namespaces[1]

    @cached_property
    def formatted_current_context(self):
        return self.current_context.replace('-', '_')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        namespace = 'doctorate' if self.current_context == 'create' else self.formatted_current_context
        context['detail_base_template'] = f'admission/{namespace}/details/tab_layout.html'
        context['form_base_template'] = f'admission/{namespace}/forms/tab_layout.html'
        context['base_namespace'] = self.base_namespace
        return context

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    @cached_property
    def admission_uuid(self):
        return str(self.kwargs.get('pk', ''))


class LoadDossierViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    detail_base_template = 'admission/doctorate/detail_tab_layout.html'
    form_base_template = 'admission/doctorate/form_tab_layout.html'

    @cached_property
    def admission(self):
        mapping = {
            'doctorate': AdmissionPropositionService.get_proposition,
            'general-education': AdmissionPropositionService.get_general_education_proposition,
            'continuing-education': AdmissionPropositionService.get_continuing_education_proposition,
        }
        return mapping[self.current_context](
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    @cached_property
    def specific_questions(self):
        mapping = {
            'doctorate': AdmissionPropositionService.retrieve_doctorate_specific_questions,
            'general-education': AdmissionPropositionService.retrieve_general_specific_questions,
            'continuing-education': AdmissionPropositionService.retrieve_continuing_specific_questions,
        }
        return mapping[self.current_context](
            person=self.request.user.person,
            uuid=self.admission_uuid,
            tab_name=self.tab_of_specific_questions,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.admission_uuid:
            context['admission'] = self.admission

            if hasattr(self, 'tab_of_specific_questions'):
                context['specific_questions'] = self.specific_questions

        return context


class LoadDoctorateViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    detail_base_template = 'admission/doctorate/detail_tab_layout.html'
    form_base_template = 'admission/doctorate/form_tab_layout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['admission'] = self.doctorate
        context['doctorate'] = self.doctorate
        # We display the information related to the doctorate instead of the admission
        context['detail_base_template'] = 'admission/doctorate/details/doctorate_tab_layout.html'

        return context

    @cached_property
    def doctorate(self):
        return AdmissionDoctorateService.get_doctorate(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
