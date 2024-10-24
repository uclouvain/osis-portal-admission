# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import resolve_url
from django.template.loader import select_template
from django.utils.datetime_safe import date
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from admission.contrib.enums import ChoixStatutPropositionDoctorale, IN_PROGRESS_STATUSES, CANCELLED_STATUSES
from admission.services.doctorate import AdmissionDoctorateService
from admission.services.proposition import AdmissionPropositionService

LATE_MESSAGE_POOLS = [
    'ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE',
    'ADMISSION_POOL_UE5_BELGIAN',
]
LATE_MESSAGE_DAYS_THRESHOLD = 31


class LoadViewMixin(LoginRequiredMixin, ContextMixin):
    @property
    def current_context(self):
        return self.request.resolver_match.namespaces[1]

    @cached_property
    def formatted_current_context(self):
        return self.current_context.replace('-', '_')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        templates = [
            f'admission/{self.formatted_current_context}/tab_layout.html',
            'admission/tab_layout.html',
        ]
        context['base_template'] = select_template(templates)
        context['base_namespace'] = self.base_namespace
        context['current_context'] = self.current_context
        context['is_general'] = self.is_general
        context['is_continuing'] = self.is_continuing
        context['is_doctorate'] = self.is_doctorate
        context['IN_PROGRESS_STATUSES'] = IN_PROGRESS_STATUSES
        context['CANCELLED_STATUSES'] = CANCELLED_STATUSES
        return context

    @property
    def is_general(self):
        return self.current_context == 'general-education'

    @property
    def is_continuing(self):
        return self.current_context == 'continuing-education'

    @property
    def is_on_create(self):
        return self.current_context == 'create'

    @property
    def is_doctorate(self):
        return self.current_context == 'doctorate'

    @cached_property
    def base_namespace(self):
        return ':'.join(self.request.resolver_match.namespaces[:2])

    @cached_property
    def admission_uuid(self):
        return str(self.kwargs.get('pk', ''))

    @cached_property
    def person(self):
        return self.request.user.person

    def _get_url(self, tab_name, update=False):
        """Return the URL for the given tab."""
        mapping = {
            'base_namespace': self.base_namespace,
            'tab_name': tab_name,
            'update': ':update' if update and self.kwargs.get('pk', None) else '',
        }
        pattern = '{base_namespace}{update}:{tab_name}'.format(**mapping)
        if self.kwargs.get('pk', None):
            return resolve_url(pattern, pk=self.admission_uuid)
        return resolve_url(pattern)


class LoadDossierViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

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

            if self.is_continuing:
                context['training_contact'] = mark_safe(
                    ', '.join(
                        f'<a href="mailto:{email}">{email}</a>'
                        for email in self.admission.adresses_emails_gestionnaires_formation
                    )
                )

            # Add info about doctorate if needed (this concerns the project/cotutelle/supervision tabs)
            if context['admission'].statut == ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name:
                context['doctorate'] = AdmissionDoctorateService.get_doctorate(
                    person=self.request.user.person,
                    uuid=self.admission_uuid,
                )

        # Late message
        if (
            self.admission_uuid
            and getattr(self.admission, 'date_fin_pot', None)
            and self.admission.pot_calcule in LATE_MESSAGE_POOLS
            and (self.admission.date_fin_pot - date.today()).days < LATE_MESSAGE_DAYS_THRESHOLD
        ):
            messages.warning(
                self.request,
                _(
                    "On the basis of the information you have provided, you are requesting consideration "
                    'of <a href="https://uclouvain.be/en/study/inscriptions/special-follow-up.html#Late_enrolment" '
                    'target="_blank">a late enrolment application</a>. This must be confirmed as soon as '
                    'possible and no '
                    "later than %(date)s. The admission panel reserves the right to accept or refuse this "
                    "late application."
                )
                % {'date': self.admission.date_fin_pot.strftime('%d/%m/%Y')},
            )
        return context


class LoadDoctorateViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['admission'] = self.doctorate
        context['doctorate'] = self.doctorate
        return context

    @cached_property
    def doctorate(self):
        return AdmissionDoctorateService.get_doctorate(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
