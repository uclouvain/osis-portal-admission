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
from typing import Optional

from django.contrib import messages
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TYPES_FORMATION_GENERALE, TypeFormation
from admission.contrib.forms.project import COMMISSIONS_CDE_CLSM, COMMISSION_CDSS, SCIENCE_DOCTORATE
from admission.contrib.forms.training_choice import TrainingChoiceForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import FormMixinWithSpecificQuestions, WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService
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
        'COMMISSIONS_CDE_CLSM': COMMISSIONS_CDE_CLSM,
        'COMMISSION_CDSS': COMMISSION_CDSS,
        'SCIENCE_DOCTORATE': SCIENCE_DOCTORATE,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_uuid: Optional[str] = None
        self.training_type: Optional[TypeFormation] = None

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
        new_data = {
            'type_admission': data.get('admission_type'),
            'justification': data.get('justification'),
            'bourse_erasmus_mundus': data.get('erasmus_mundus_scholarship'),
        }
        if not self.admission_uuid:
            [training_acronym, training_year] = split_training_id(data.get('doctorate_training'))
            new_data['sigle_formation'] = training_acronym
            new_data['annee_formation'] = int(training_year)
            new_data['commission_proximite'] = (
                data.get('proximity_commission_cde')
                or data.get('proximity_commission_cdss')
                or data.get('science_sub_domain')
                or ''
            )
        return new_data

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
        messages.info(self.request, _("Your data has been saved"))

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
                'erasmus_mundus_scholarship': (
                    self.admission.bourse_erasmus_mundus and self.admission.bourse_erasmus_mundus.uuid
                ),
                'proximity_commission': self.admission.commission_proximite,
                'specific_question_answers': self.admission.reponses_questions_specifiques,
            }
        elif self.current_context == 'general-education':
            return {
                'general_education_training': get_training_id(self.admission.formation),
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
            }
        elif self.current_context == 'continuing-education':
            return {
                'mixed_training': get_training_id(self.admission.formation),
                'specific_question_answers': self.admission.reponses_questions_specifiques,
            }
