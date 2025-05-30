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
from django.core.exceptions import PermissionDenied
from django.views.generic import FormView

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from admission.contrib.enums.financement import ChoixTypeFinancement
from admission.contrib.forms.project import DoctorateAdmissionProjectForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import (
    AdmissionPropositionService,
    PropositionBusinessException,
)

__all__ = ['DoctorateAdmissionProjectFormView']


class DoctorateAdmissionProjectFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/forms/project.html'
    proposition = None
    error_mapping = {
        PropositionBusinessException.JustificationRequiseException: 'justification',
        PropositionBusinessException.ContratTravailInconsistantException: 'type_contrat_travail',
        PropositionBusinessException.DoctoratNonTrouveException: 'doctorate',
        PropositionBusinessException.InstitutionInconsistanteException: 'institution',
        PropositionBusinessException.DomaineTheseInconsistantException: 'domaine_these',
    }
    form_class = DoctorateAdmissionProjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['admission_type'] = self.admission.type_admission
        return kwargs

    def get_initial(self):
        if 'url' not in self.admission.links['update_project']:
            raise PermissionDenied(self.admission.links['update_project']['error'])
        return {
            **self.admission.to_dict(),
            'bourse_recherche': self.admission.bourse_recherche and self.admission.bourse_recherche['uuid'],
        }

    def prepare_data(self, data):
        # Process the form data to match API
        if self.admission.type_admission != AdmissionType.PRE_ADMISSION.name:
            data['justification'] = ''

        if data['type_financement'] != ChoixTypeFinancement.WORK_CONTRACT.name:
            data['type_contrat_travail'] = ''
            data['eft'] = None

        if data['type_financement'] != ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            data['bourse_recherche'] = ''
            data['autre_bourse_recherche'] = ''
            data['bourse_date_debut'] = None
            data['bourse_date_fin'] = None
            data['bourse_preuve'] = []

        if not data['type_financement']:
            data['duree_prevue'] = None
            data['temps_consacre'] = None

        if data['doctorat_deja_realise'] not in [
            ChoixDoctoratDejaRealise.YES.name,
        ]:
            data['institution'] = ''
            data['domaine_these'] = ''
            data['non_soutenue'] = None
            data['date_soutenance'] = None
            data['raison_non_soutenue'] = ''

        if data['non_soutenue']:
            data['date_soutenance'] = None
        else:
            data['raison_non_soutenue'] = ''

        return data

    def call_webservice(self, data):
        data['uuid'] = self.admission_uuid
        AdmissionPropositionService.update_proposition(person=self.person, **data)
