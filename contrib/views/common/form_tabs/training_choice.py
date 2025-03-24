# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import Optional

from django.contrib import messages
from django.shortcuts import redirect, resolve_url
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.constants import MED_DENT_TRAINING_DOMAIN_REGEX
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import (
    OSIS_ADMISSION_EDUCATION_TYPES_MAPPING,
    TYPES_FORMATION_GENERALE,
    TypeFormation,
)
from admission.contrib.forms.project import (
    COMMISSION_CDSS,
    COMMISSIONS_CDE_CLSM,
    SCIENCE_DOCTORATE,
)
from admission.contrib.forms.training_choice import TrainingChoiceForm, get_training
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import (
    FormMixinWithSpecificQuestions,
    WebServiceFormMixin,
)
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import can_make_action
from admission.utils import get_training_id, split_training_id

NAMESPACE_KEY_BY_ADMISSION_TYPE = {
    TypeFormation.BACHELIER.name: 'general-education',
    TypeFormation.MASTER.name: 'general-education',
    TypeFormation.DOCTORAT.name: 'doctorate',
    TypeFormation.AGREGATION_CAPES.name: 'general-education',
    TypeFormation.FORMATION_CONTINUE.name: 'continuing-education',
    TypeFormation.CERTIFICAT.name: 'general-education',
}

__all__ = ['AdmissionTrainingChoiceFormView']


class AdmissionTrainingChoiceFormView(
    LoadDossierViewMixin,
    FormMixinWithSpecificQuestions,
    WebServiceFormMixin,
    FormView,
):
    template_name = 'admission/forms/training_choice.html'
    tab_of_specific_questions = Onglets.CHOIX_FORMATION.name
    form_class = TrainingChoiceForm
    extra_context = {
        'GENERAL_EDUCATION_TYPES': list(TYPES_FORMATION_GENERALE),
        'CONTINUING_EDUCATION_TYPES': OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.FORMATION_CONTINUE.name],
        'COMMISSIONS_CDE_CLSM': COMMISSIONS_CDE_CLSM,
        'COMMISSION_CDSS': COMMISSION_CDSS,
        'SCIENCE_DOCTORATE': SCIENCE_DOCTORATE,
        'MED_DENT_TRAINING_DOMAIN_REGEX': MED_DENT_TRAINING_DOMAIN_REGEX,
    }
    NOT_IN_SPECIFIC_ENROLMENT_PERIODS_MESSAGES = {
        'medicine_dentistry_bachelor': _(
            'Pending the publication of the results of the medical and dental entrance examination, your application '
            'can only be submitted from %(start_date)s.'
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_uuid: Optional[str] = None
        self.training_type: Optional[TypeFormation] = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # A message is displayed for the HUE candidates for a continuing education training
        if self.is_on_create:
            identification_dto = AdmissionPersonService.retrieve_identification_dto(person=self.request.user.person)
            context['candidate_has_ue_nationality'] = identification_dto.pays_nationalite_europeen

        elif self.is_continuing:
            context['candidate_has_ue_nationality'] = self.admission.pays_nationalite_ue_candidat

        if self.is_on_create or self.is_general:
            # Some messages are displayed when we are outside of some specific enrolment periods
            specific_enrolment_periods = AdmissionPropositionService.retrieve_specific_enrolment_periods(
                person=self.request.user.person
            )
            today_date = datetime.date.today()

            context['not_in_specific_enrolment_periods_messages'] = {}
            for period_key, message in self.NOT_IN_SPECIFIC_ENROLMENT_PERIODS_MESSAGES.items():
                period = getattr(specific_enrolment_periods, period_key, None)

                if period and not (period.date_debut <= today_date <= period.date_fin):
                    context['not_in_specific_enrolment_periods_messages'][period_key] = message % {
                        'start_date': date_format(period.date_debut, 'j F Y'),
                        'end_date': date_format(period.date_fin, 'j F Y'),
                    }

        return context

    def dispatch(self, request, *args, **kwargs):
        # Check permission
        if self.current_context == 'general-education':
            AdmissionPropositionService.get_general_education_training_choice(
                self.request.user.person,
                uuid=self.admission_uuid,
            )
        elif self.current_context == 'continuing-education':
            AdmissionPropositionService.get_continuing_education_training_choice(
                self.request.user.person,
                uuid=self.admission_uuid,
            )
        elif self.is_doctorate and not can_make_action(self.admission, 'update_training_choice'):
            return redirect('admission:doctorate:training-choice', pk=self.admission_uuid)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['current_context'] = self.current_context
        if self.admission_uuid:
            kwargs['admission_uuid'] = self.admission_uuid
        return kwargs

    def prepare_data(self, data):
        new_data = {}
        self.training_type = data.get('training_type')
        if self.training_type == TypeFormation.DOCTORAT.name:
            new_data = self.prepare_data_for_doctorate(data)
        elif self.training_type == TypeFormation.FORMATION_CONTINUE.name:
            new_data = self.prepare_data_for_continuing_education(data)
        elif self.training_type in TYPES_FORMATION_GENERALE:
            new_data = self.prepare_data_for_general_education(data)
        if self.admission_uuid:
            new_data['uuid_proposition'] = self.admission_uuid
            new_data['reponses_questions_specifiques'] = data.get('specific_question_answers')
        else:
            new_data['matricule_candidat'] = self.person.global_id
        return new_data

    def prepare_data_for_doctorate(self, data):
        prepared_data = {
            'type_admission': data.get('admission_type'),
            'justification': data.get('justification'),
            'sigle_formation': '',
            'annee_formation': None,
            'commission_proximite': (
                data.get('proximity_commission_cde')
                or data.get('proximity_commission_cdss')
                or data.get('science_sub_domain')
                or ''
            ),
        }

        if data.get('doctorate_training'):
            [training_acronym, training_year] = split_training_id(data.get('doctorate_training'))
            prepared_data['sigle_formation'] = training_acronym
            prepared_data['annee_formation'] = int(training_year)

        if self.is_on_create:
            prepared_data['pre_admission_associee'] = data.get('related_pre_admission')

        return prepared_data

    def prepare_data_for_general_education(self, data):
        [training_acronym, training_year] = split_training_id(data.get('general_education_training'))
        return {
            'sigle_formation': training_acronym,
            'annee_formation': int(training_year),
            'bourse_erasmus_mundus': data.get('erasmus_mundus_scholarship'),
            'bourse_double_diplome': data.get('double_degree_scholarship'),
            'bourse_internationale': data.get('international_scholarship'),
        }

    def prepare_data_for_continuing_education(self, data):
        [training_acronym, training_year] = split_training_id(data.get('mixed_training'))
        return {
            'sigle_formation': training_acronym,
            'annee_formation': int(training_year),
            'motivations': data.get('motivations'),
            'moyens_decouverte_formation': data.get('ways_to_find_out_about_the_course'),
            'autre_moyen_decouverte_formation': data.get('other_way_to_find_out_about_the_course'),
            'marque_d_interet': data.get('interested_mark'),
        }

    def call_webservice(self, data):
        if self.current_context == 'create':
            # Update the proposition
            namespace = NAMESPACE_KEY_BY_ADMISSION_TYPE[self.training_type].replace('-', '_')
            method = getattr(AdmissionPropositionService, f"create_{namespace}_proposition")
            response = method(person=self.person, data=data)
            self.created_uuid = response.get('uuid')
        else:
            # Update the choice
            {
                'doctorate': AdmissionPropositionService.update_doctorate_education_choice,
                'general-education': AdmissionPropositionService.update_general_education_choice,
                'continuing-education': AdmissionPropositionService.update_continuing_education_choice,
            }[self.current_context](
                person=self.person,
                uuid=self.admission_uuid,
                data=data,
            )

    def get_success_url(self):
        messages.info(self.request, _("Your data have been saved"))

        # If a url to redirect is specified in the request, use it
        if self.request.POST.get('redirect_to'):
            return self.request.POST.get('redirect_to')

        next_context = NAMESPACE_KEY_BY_ADMISSION_TYPE.get(self.training_type)
        tab_to_redirect = (
            self.get_next_tab_name(for_context=next_context)
            # Redirect on next tab in tab list if submit_and_continue
            if '_submit_and_continue' in self.request.POST
            else self.request.resolver_match.url_name
        )
        return resolve_url(
            'admission:{namespace}:update:{tab_name}'.format(
                namespace=next_context,
                tab_name=tab_to_redirect,
            ),
            pk=self.created_uuid or self.admission_uuid,
        )

    def get_initial(self):
        if self.current_context == 'doctorate':
            return {
                'admission_type': self.admission.type_admission,
                'justification': self.admission.justification,
                'sector': self.admission.code_secteur_formation,
                'doctorate_training': get_training_id(self.admission.doctorat),
                'proximity_commission': self.admission.commission_proximite,
                'specific_question_answers': self.admission.reponses_questions_specifiques,
                'campus': self.admission.doctorat['campus_uuid'],
            }
        elif self.current_context == 'general-education':
            training_id = get_training_id(self.admission.formation)
            training = get_training(person=self.person, training=training_id)
            training_key = (
                'mixed_training'
                if training['education_group_type']
                in OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.CERTIFICAT.name]
                else 'general_education_training'
            )
            return {
                training_key: training_id,
                'double_degree_scholarship': (
                    self.admission.bourse_double_diplome and self.admission.bourse_double_diplome.uuid
                ),
                'international_scholarship': (
                    self.admission.bourse_internationale and self.admission.bourse_internationale.uuid
                ),
                'erasmus_mundus_scholarship': (
                    self.admission.bourse_erasmus_mundus and self.admission.bourse_erasmus_mundus.uuid
                ),
                'specific_question_answers': self.admission.reponses_questions_specifiques,
                'campus': self.admission.formation['campus_uuid'],
            }
        elif self.current_context == 'continuing-education':
            return {
                'mixed_training': get_training_id(self.admission.formation),
                'specific_question_answers': self.admission.reponses_questions_specifiques,
                'motivations': self.admission.motivations,
                'ways_to_find_out_about_the_course': self.admission.moyens_decouverte_formation,
                'other_way_to_find_out_about_the_course': self.admission.autre_moyen_decouverte_formation,
                'interested_mark': self.admission.marque_d_interet,
                'campus': self.admission.formation['campus_uuid'],
            }
