# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import resolve_url
from django.utils.translation import get_language
from django.views.generic import FormView

from admission.contrib.enums.financement import BourseRecherche, ChoixTypeContratTravail
from admission.contrib.forms.project import DoctorateAdmissionProjectCreateForm, DoctorateAdmissionProjectForm
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, PropositionBusinessException
from osis_document.api.utils import get_remote_token


class DoctorateAdmissionProjectFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_project.html'
    proposition = None
    error_mapping = {
        PropositionBusinessException.JustificationRequiseException: 'justification',
        PropositionBusinessException.ProximityCommissionInconsistantException: 'doctorate',
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
            self.proposition = AdmissionPropositionService.get_proposition(
                person=self.person,
                uuid=str(self.kwargs['pk']),
            )
            initial = {
                **self.proposition.to_dict(),
                'sector': self.proposition.code_secteur_formation,
                'doctorate': "{sigle}-{annee}".format(
                    sigle=self.proposition.sigle_doctorat,
                    annee=self.proposition.annee_doctorat,
                ),
            }
            document_fields = [
                'documents_projet',
                'graphe_gantt',
                'proposition_programme_doctoral',
                'projet_formation_complementaire',
                'lettres_recommandation',
            ]
            for field in document_fields:
                initial[field] = [get_remote_token(document, write_token=True)
                                  for document in getattr(self.proposition, field)]
            return initial
        return super().get_initial()

    def prepare_data(self, data):
        # Process the form data to match API
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
            data.get('commission_proximite_cde')
            if data.get('commission_proximite_cde') != ''
            else data.get('commission_proximite_cdss')
        )
        data.pop('type_contrat_travail_other')
        data.pop('bourse_recherche_other')
        data.pop('commission_proximite_cde')
        data.pop('commission_proximite_cdss')

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
            AdmissionPropositionService.create_proposition(person=self.person, **data)
        else:
            data['uuid'] = str(self.kwargs['pk'])
            AdmissionPropositionService.update_proposition(person=self.person, **data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_update_form:
            context['admission'] = self.proposition
            # Lookup sector label from API
            attr_name = 'intitule_fr' if get_language() == settings.LANGUAGE_CODE else 'intitule_en'
            context['sector_label'] = [
                getattr(s, attr_name) for s in AdmissionAutocompleteService.get_sectors(self.request.user.person)
                if s.sigle == self.proposition.code_secteur_formation
            ][0]
        return context

    def get_success_url(self):
        if hasattr(self, 'response'):
            return resolve_url('admission:doctorate-detail:project', pk=self.response.uuid)
        return super().get_success_url()
