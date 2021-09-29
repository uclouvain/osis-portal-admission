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
from django.urls import reverse_lazy
from django.views.generic import FormView
from osis_document.api.utils import get_remote_token

from admission.contrib.enums.financement import BourseRecherche, ChoixTypeContratTravail
from admission.contrib.forms.projet import DoctorateAdmissionProjectCreateForm, DoctorateAdmissionProjectForm
from admission.services.proposition import AdmissionPropositionService
from osis_admission_sdk.exceptions import ApiException

__all__ = [
    # "DoctorateAdmissionConfirmFormView",
    # "DoctorateAdmissionConfirmPaperFormView",
    # "DoctorateAdmissionJuryFormView",
    # "DoctorateAdmissionPrivateDefenseFormView",
    "DoctorateAdmissionProjectFormView",
    # "DoctorateAdmissionPublicDefenseFormView",
    # "DoctorateAdmissionSupervisionFormView",
    # "DoctorateAdmissionTrainingFormView",
]


class DoctorateAdmissionProjectFormView(FormView):
    template_name = 'admission/doctorate/form_tab_project.html'
    success_url = reverse_lazy('admission:doctorate-list')
    proposition = None

    @property
    def is_update_form(self):
        return 'pk' in self.kwargs

    def get_form_class(self):
        if self.is_update_form:
            return DoctorateAdmissionProjectForm
        return DoctorateAdmissionProjectCreateForm

    def get_initial(self):
        if self.is_update_form:
            self.proposition = AdmissionPropositionService.get_proposition(uuid=str(self.kwargs['pk']))
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
            ]
            for field in document_fields:
                initial[field] = [get_remote_token(document, write_token=True)
                                  for document in getattr(self.proposition, field)]
            return initial
        return super().get_initial()

    def form_valid(self, form):
        data = dict(**form.cleaned_data)

        # Process the form data to match API
        data['bureau_cde'] = data['bureau_cde'] or None
        data['type_contrat_travail'] = (
            data['type_contrat_travail_other']
            if data['type_contrat_travail'] == ChoixTypeContratTravail.OTHER.name
            else data['type_contrat_travail']
        )
        data['bourse_recherche'] = (
            data['bourse_recherche_other'] if data['bourse_recherche'] == BourseRecherche.OTHER.name
            else data['bourse_recherche']
        )
        del data['type_contrat_travail_other']
        del data['bourse_recherche_other']

        try:
            self.call_webservice(data)
        except ApiException as e:
            # Put errors on the correct fields
            if e.status == 400:
                import json
                error_mapping = json.loads(e.body)
                for field, errors in error_mapping.items():
                    if field == 'non_field_errors':
                        field = None
                    for error in errors:
                        form.add_error(field, error['detail'])
                return self.form_invalid(form)
            else:
                raise e
        return super().form_valid(form)

    def call_webservice(self, data):
        if not self.is_update_form:
            doctorate_value = data.pop('doctorate', '')
            data = dict(
                **data,
                sigle_formation=doctorate_value.split('-')[0],
                annee_formation=int(doctorate_value.split('-')[-1]),
                matricule_candidat=self.request.user.person.global_id,
            )
            del data['sector']
            AdmissionPropositionService.create_proposition(**data)
        else:
            data['uuid'] = str(self.kwargs['pk'])
            AdmissionPropositionService.update_proposition(**data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_update_form:
            context['admission'] = self.proposition
        return context

# class DoctorateAdmissionSupervisionFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionJuryFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionConfirmFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionConfirmPaperFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionTrainingFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionPrivateDefenseFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
#
#
# class DoctorateAdmissionPublicDefenseFormView(UpdateView):
#     model = DoctorateAdmission
#     form_class = DoctorateAdmissionProjectForm
#     template_name = 'admission/doctorate/form_tab_project.html'
#
#     def get_object(self, queryset=None):
#         return self.request.user.person
