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
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from admission.contrib.enums.financement import BourseRecherche, ChoixTypeContratTravail, ChoixTypeFinancement
from admission.contrib.forms.project import (
    COMMISSIONS_CDE_CLSM,
    COMMISSION_CDSS,
    DoctorateAdmissionProjectCreateForm,
    DoctorateAdmissionProjectForm,
    SCIENCE_DOCTORATE,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, PropositionBusinessException


class DoctorateAdmissionProjectFormView(
    LoadDossierViewMixin,
    WebServiceFormMixin,
    FormView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/forms/project.html'
    proposition = None
    error_mapping = {
        PropositionBusinessException.JustificationRequiseException: 'justification',
        PropositionBusinessException.ProximityCommissionInconsistantException: None,
        PropositionBusinessException.ContratTravailInconsistantException: 'type_contrat_travail',
        PropositionBusinessException.DoctoratNonTrouveException: 'doctorate',
        PropositionBusinessException.InstitutionInconsistanteException: 'institution',
    }

    @property
    def is_update_form(self):
        return 'pk' in self.kwargs

    def get_form_class(self):
        if self.is_update_form:
            return DoctorateAdmissionProjectForm
        return DoctorateAdmissionProjectCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        return kwargs

    def get_initial(self):
        if self.is_update_form:
            if 'url' not in self.admission.links['update_proposition']:
                raise PermissionDenied(self.admission.links['update_proposition']['error'])
            return {
                **self.admission.to_dict(),
                'sector': self.admission.code_secteur_formation,
                'doctorate': "{sigle}-{annee}".format(
                    sigle=self.admission.sigle_doctorat,
                    annee=self.admission.annee_doctorat,
                ),
            }
        return super().get_initial()

    def prepare_data(self, data):
        # Process the form data to match API
        if data['type_admission'] != AdmissionType.PRE_ADMISSION.name:
            data['justification'] = ''

        if data['type_financement'] != ChoixTypeFinancement.WORK_CONTRACT.name:
            data['type_contrat_travail'] = ''
            data['type_contrat_travail_other'] = ''
            data['eft'] = None

        if data['type_financement'] != ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
            data['bourse_recherche'] = ''
            data['bourse_recherche_other'] = ''

        if not data['type_financement']:
            data['duree_prevue'] = None
            data['temps_consacre'] = None

        if data['doctorat_deja_realise'] not in [
            ChoixDoctoratDejaRealise.YES.name,
            ChoixDoctoratDejaRealise.PARTIAL.name,
        ]:
            data['institution'] = ''
            data['non_soutenue'] = None
            data['date_soutenance'] = None
            data['raison_non_soutenue'] = ''

        if data['non_soutenue']:
            data['date_soutenance'] = None
        else:
            data['raison_non_soutenue'] = ''

        data['type_contrat_travail'] = (
            data['type_contrat_travail_other']
            if data['type_contrat_travail'] == ChoixTypeContratTravail.OTHER.name
            else data['type_contrat_travail']
        )
        data['bourse_recherche'] = (
            data['bourse_recherche_other']
            if data['bourse_recherche'] == BourseRecherche.OTHER.name
            else data['bourse_recherche']
        )
        data['commission_proximite'] = (
            data.get('commission_proximite_cde') or data.get('commission_proximite_cdss') or data.get('sous_domaine')
        )
        data.pop('type_contrat_travail_other')
        data.pop('bourse_recherche_other')
        data.pop('commission_proximite_cde')
        data.pop('commission_proximite_cdss')
        data.pop('sous_domaine')

        return data

    def call_webservice(self, data):
        if not self.is_update_form:
            doctorate_value = data.pop('doctorate', '')
            data = dict(
                **data,
                sigle_formation=doctorate_value.split('-')[0],
                annee_formation=int(doctorate_value.split('-')[-1]),
                matricule_candidat=self.person.global_id,
            )
            data.pop('sector')
            response = AdmissionPropositionService.create_proposition(person=self.person, **data)
            self.uuid = response['uuid']
        else:
            data['uuid'] = self.admission_uuid
            AdmissionPropositionService.update_proposition(person=self.person, **data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['COMMISSIONS_CDE_CLSM'] = COMMISSIONS_CDE_CLSM
        context['COMMISSION_CDSS'] = COMMISSION_CDSS
        context['SCIENCE_DOCTORATE'] = SCIENCE_DOCTORATE
        if self.is_update_form:
            # Lookup sector label from API
            context['sector_label'] = [
                s.intitule
                for s in AdmissionAutocompleteService.get_sectors(self.request.user.person)
                if s.sigle == self.admission.code_secteur_formation
            ][0]
        return context

    def get_success_url(self):
        if self.admission_uuid:
            return super().get_success_url()
        # On creation, display a message and redirect on same form (but with uuid now that we have it)
        messages.info(self.request, _("Your data has been saved"))
        return resolve_url('admission:doctorate:update:project', pk=self.uuid)
