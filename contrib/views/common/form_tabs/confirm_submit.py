# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.shortcuts import redirect, resolve_url
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.generic import FormView

from admission.constants import PROPOSITION_JUST_SUBMITTED
from admission.contrib.enums import ChoixStatutPropositionGenerale
from admission.contrib.forms.confirm_submit import AdmissionConfirmSubmitForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import (
    ADDITIONAL_BUSINESS_EXCEPTIONS,
    TAB_OF_BUSINESS_EXCEPTION,
    AdmissionPropositionService,
)
from admission.templatetags.admission import TAB_TREES, can_read_tab

__all__ = [
    'AdmissionConfirmSubmitFormView',
]


class AdmissionConfirmSubmitFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/forms/confirm-submit.html'
    service_mapping = {
        'doctorate': (
            AdmissionPropositionService.verify_proposition,
            AdmissionPropositionService.submit_proposition,
        ),
        'general-education': (
            AdmissionPropositionService.verify_general_proposition,
            AdmissionPropositionService.submit_general_proposition,
            AdmissionPropositionService.specify_reason_multiple_applications_same_cycle_same_year,
        ),
        'continuing-education': (
            AdmissionPropositionService.verify_continuing_proposition,
            AdmissionPropositionService.submit_continuing_proposition,
        ),
    }
    form_class = AdmissionConfirmSubmitForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.submit_proposition_result = {}

    def get_initial(self):
        initial_data = {
            'pool': self.admission.pot_calcule,
            'annee': self.admission.annee_calculee,
        }

        if self.is_general:
            initial_data['raison_plusieurs_demandes_meme_cycle_meme_annee'] = (
                self.admission.raison_plusieurs_demandes_meme_cycle_meme_annee
            )
            initial_data['justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee'] = (
                self.admission.justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee
            )

        return initial_data

    def form_invalid(self, form):
        # If the form contains non_field errors, webservice has failed, redirect with error message
        if form.errors.get('__all__'):
            messages.error(self.request, _("An error has occurred, please check fields and try again."))
            return redirect(self.request.get_full_path())

        # Else reset the form values and redisplay form
        form = self.get_form_class()(**{**self.get_form_kwargs(), 'data': None})
        return super().form_invalid(form)

    @cached_property
    def confirmation_conditions(self):
        """Retrieve the missing confirmation conditions or elements"""
        return self.service_mapping[self.current_context][0](
            person=self.person,
            uuid=self.admission_uuid,
        ).to_dict()

    def get_context_data(self, **kwargs):
        # It is important to get the errors before loading admission data
        context = super().get_context_data(**kwargs)
        context['confirmation_form'] = context.pop('form')
        context['additional_conditions'] = additional_conditions = {}

        # Group the missing conditions by tab or add them to the additional conditions dictionary if any
        if self.confirmation_conditions['errors']:
            errors_by_tab = {
                tab.name: {'label': tab.label, 'errors': {}}
                for child_tabs in TAB_TREES[self.current_context].values()
                for tab in child_tabs
                if can_read_tab(self.admission, tab)
            }
            for error in self.confirmation_conditions['errors']:
                # Additional conditions
                if error['status_code'] in ADDITIONAL_BUSINESS_EXCEPTIONS:
                    additional_conditions[error['status_code']] = error['detail']
                    continue

                # Tab related conditions
                tab_name = TAB_OF_BUSINESS_EXCEPTION[error['status_code']]
                if error['status_code'] not in errors_by_tab[tab_name]['errors']:
                    errors_by_tab[tab_name]['errors'][error['status_code']] = []
                errors_by_tab[tab_name]['errors'][error['status_code']].append(error['detail'])

            context['missing_confirmation_conditions'] = errors_by_tab
            context['missing_confirmations_conditions_number'] = len(self.confirmation_conditions['errors']) - len(
                additional_conditions
            )

        context['access_conditions_url'] = self.confirmation_conditions.get('access_conditions_url')
        context['pool_start_date'] = self.confirmation_conditions.get('pool_start_date')
        context['pool_end_date'] = self.confirmation_conditions.get('pool_end_date')
        context['calendar_url'] = (
            "https://uclouvain.be/fr/etudier/inscriptions/calendrier-inscriptions.html"
            if get_language() == settings.LANGUAGE_CODE
            else "https://uclouvain.be/en/study/inscriptions/calendrier-inscriptions.html"
        )
        context['special_fields'] = [
            "hors_delai",
            "justificatifs",
            "declaration_sur_lhonneur",
            "droits_inscription_iufc",
            "raison_plusieurs_demandes_meme_cycle_meme_annee",
            "justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee",
        ]

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        admission = self.admission
        kwargs['elements'] = self.confirmation_conditions.get('elements_confirmation')
        kwargs['display_several_applications_same_cycle_same_year_questions'] = self.confirmation_conditions.get(
            'display_several_applications_same_cycle_same_year_questions',
        )
        kwargs['training'] = admission.doctorat if hasattr(admission, 'doctorat') else admission.formation
        return kwargs

    def get_success_url(self):
        if 'multiple-applications-form' in self.request.POST:
            return self.request.get_full_path()

        if self.submit_proposition_result.get('status') == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name:
            return resolve_url(f'admission:{self.current_context}:payment', pk=self.admission_uuid)

        self.request.session[PROPOSITION_JUST_SUBMITTED] = self.current_context
        return resolve_url(f'admission:{self.current_context}', pk=self.admission_uuid)

    def prepare_data(self, data):
        prepared_data = {
            'pool': data.pop('pool'),
            'annee': data.pop('annee'),
        }

        if self.is_general:
            prepared_data['raison_plusieurs_demandes_meme_cycle_meme_annee'] = data.pop(
                'raison_plusieurs_demandes_meme_cycle_meme_annee',
                '',
            )
            prepared_data['justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee'] = data.pop(
                'justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee',
                '',
            )

        prepared_data['elements_confirmation'] = data

        return prepared_data

    def call_webservice(self, data):
        service_to_call_number = 2 if 'multiple-applications-form' in self.request.POST else 1
        self.submit_proposition_result = self.service_mapping[self.current_context][service_to_call_number](
            person=self.person,
            uuid=self.admission_uuid,
            **data,
        ).to_dict()
