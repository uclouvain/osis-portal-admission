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
from typing import Optional

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.enums.training_choice import TYPES_FORMATION_GENERALE, TypeFormation
from admission.contrib.forms.project import COMMISSIONS_CDE_CLSM, COMMISSION_CDSS, SCIENCE_DOCTORATE
from admission.contrib.forms.training_choice import TrainingChoiceForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService
from admission.utils import split_training_id


class AdmissionTrainingChoiceFormView(
    LoadDossierViewMixin,
    WebServiceFormMixin,
    FormView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/admission/forms/training_choice.html'
    form_class = TrainingChoiceForm

    extra_context = {
        'GENERAL_EDUCATION_TYPES': list(TYPES_FORMATION_GENERALE),
        'COMMISSIONS_CDE_CLSM': COMMISSIONS_CDE_CLSM,
        'COMMISSION_CDSS': COMMISSION_CDSS,
        'SCIENCE_DOCTORATE': SCIENCE_DOCTORATE,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid: Optional[str] = None
        self.training_type: Optional[TypeFormation] = None

    @property
    def is_update_form(self):
        return self.admission_uuid != ''

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['on_update'] = self.is_update_form
        return kwargs

    def get_initial(self):
        if self.is_update_form:
            if 'url' not in self.admission.links['update_proposition']:
                raise PermissionDenied(self.admission.links['update_proposition']['error'])
        return super().get_initial()

    def prepare_data(self, data):
        self.training_type = data.get('training_type')
        if self.training_type == TypeFormation.DOCTORAT.name:
            [training_acronym, training_year] = split_training_id(data.get('doctorate_training'))
            proximity_commission = (
                data.get('proximity_commission_cde')
                or data.get('proximity_commission_cdss')
                or data.get('science_sub_domain')
                or ''
            )

            return {
                'type_admission': data.get('admission_type'),
                'sigle_formation': training_acronym,
                'annee_formation': int(training_year),
                'matricule_candidat': self.person.global_id,
                'justification': data.get('justification'),
                'commission_proximite': proximity_commission,
                'bourse_erasmus_mundus': data.get('erasmus_mundus_scholarship'),
            }
        elif self.training_type == TypeFormation.FORMATION_CONTINUE.name:
            [training_acronym, training_year] = split_training_id(data.get('continuing_education_training'))
            return {
                'sigle_formation': training_acronym,
                'annee_formation': int(training_year),
                'matricule_candidat': self.person.global_id,
            }
        elif self.training_type in TYPES_FORMATION_GENERALE:
            [training_acronym, training_year] = split_training_id(data.get('general_education_training'))
            return {
                'sigle_formation': training_acronym,
                'annee_formation': int(training_year),
                'matricule_candidat': self.person.global_id,
                'bourse_erasmus_mundus': data.get('erasmus_mundus_scholarship'),
                'bourse_double_diplome': data.get('double_degree_scholarship'),
                'bourse_internationale': data.get('international_scholarship'),
            }

    def call_webservice(self, data):
        response = {}
        if self.training_type == TypeFormation.DOCTORAT.name:
            if self.is_update_form:
                pass
            else:
                response = AdmissionPropositionService.create_doctorate_proposition(person=self.person, data=data)
        elif self.training_type == TypeFormation.FORMATION_CONTINUE.name:
            if self.is_update_form:
                pass
            else:
                response = AdmissionPropositionService.create_continuing_education_choice(person=self.person, data=data)
        elif self.training_type in TYPES_FORMATION_GENERALE:
            if self.is_update_form:
                pass
            else:
                response = AdmissionPropositionService.create_general_education_choice(person=self.person, data=data)
        self.uuid = response.get('uuid')

    def get_success_url(self):
        if self.is_update_form:
            return super().get_success_url()

        # On creation, display a message and redirect on the right form and with the uuid of the created proposition
        messages.info(self.request, _("Your data has been saved"))

        # TODO redirect to the right url
        return resolve_url('admission:doctorate:update:project', pk=self.uuid)
