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
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import View
from django.views.generic import FormView

__all__ = [
    "DoctorateAdmissionJuryMemberRemoveView",
    "DoctorateAdmissionJuryMembreUpdateFormView",
    "DoctorateAdmissionJuryMemberChangeRoleView",
]

__namespace__ = {'jury-member': 'jury-member/<uuid:member_pk>'}

from admission.contrib.forms.jury.membre import JuryMembreForm
from admission.contrib.forms.jury.membre_role import JuryMembreRoleForm
from admission.contrib.views.doctorate.jury import LoadJuryViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionJuryService, JuryBusinessException
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException
from reference.models.country import Country


class LoadJuryMemberViewMixin(LoadJuryViewMixin):
    @cached_property
    def membre(self):
        return AdmissionJuryService.retrieve_jury_member(
            person=self.request.user.person,
            uuid=self.admission_uuid,
            member_uuid=self.member_uuid,
        )

    @cached_property
    def member_uuid(self):
        return str(self.kwargs.get('member_pk', ''))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['member'] = self.membre
        return context


class DoctorateAdmissionJuryMembreUpdateFormView(LoadJuryMemberViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'update'
    template_name = 'admission/doctorate/forms/jury/member_update.html'
    form_class = JuryMembreForm
    error_mapping = {
        JuryBusinessException.NonDocteurSansJustificationException: "justification_non_docteur",
        JuryBusinessException.MembreExterneSansInstitutionException: "institution",
        JuryBusinessException.MembreExterneSansPaysException: "pays",
        JuryBusinessException.MembreExterneSansNomException: "nom",
        JuryBusinessException.MembreExterneSansPrenomException: "prenom",
        JuryBusinessException.MembreExterneSansTitreException: "titre",
        JuryBusinessException.MembreExterneSansGenreException: "genre",
        JuryBusinessException.MembreExterneSansEmailException: "email",
        JuryBusinessException.MembreDejaDansJuryException: "matricule",
    }

    def get_success_url(self):
        return reverse('admission:doctorate:jury', kwargs={'pk': self.admission_uuid})

    def get_initial(self):
        if self.membre.matricule:
            institution_principale = JuryMembreForm.InstitutionPrincipaleChoices.UCL.name
        else:
            institution_principale = JuryMembreForm.InstitutionPrincipaleChoices.OTHER.name
        return {
            'matricule': self.membre.matricule,
            'institution_principale': institution_principale,
            'institution': self.membre.institution,
            'autre_institution': self.membre.autre_institution,
            'pays': Country.objects.get(name=self.membre.pays) if self.membre.pays else None,
            'nom': self.membre.nom,
            'prenom': self.membre.prenom,
            'titre': self.membre.titre,
            'justification_non_docteur': self.membre.justification_non_docteur,
            'genre': self.membre.genre,
            'email': self.membre.email,
        }

    def call_webservice(self, data):
        return AdmissionJuryService.update_jury_member(
            person=self.person,
            uuid=self.admission_uuid,
            member_uuid=self.member_uuid,
            **data,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'url' not in context['admission'].links['update_jury_preparation']:
            raise PermissionDenied(context['admission'].links['update_jury_preparation']['error'])
        return context


class DoctorateAdmissionJuryMemberRemoveView(LoadJuryMemberViewMixin, WebServiceFormMixin, View):
    urlpatterns = 'remove'

    def post(self, request, *args, **kwargs):
        try:
            AdmissionJuryService.remove_jury_member(
                person=self.person,
                uuid=self.admission_uuid,
                member_uuid=self.member_uuid,
            )
        except MultipleApiBusinessException as multiple_business_api_exception:
            for exception in multiple_business_api_exception.exceptions:
                messages.error(request, exception.detail)
        except PermissionDenied as e:
            messages.error(request, str(e))
        return redirect('admission:doctorate:jury', pk=self.admission_uuid)


class DoctorateAdmissionJuryMemberChangeRoleView(LoadJuryMemberViewMixin, WebServiceFormMixin, View):
    urlpatterns = 'change-role'

    def post(self, request, *args, **kwargs):
        form = JuryMembreRoleForm(data=request.POST)
        if form.is_valid():
            try:
                AdmissionJuryService.update_role_jury_member(
                    person=self.person,
                    uuid=self.admission_uuid,
                    member_uuid=self.member_uuid,
                    **form.cleaned_data,
                )
            except MultipleApiBusinessException as multiple_business_api_exception:
                for exception in multiple_business_api_exception.exceptions:
                    messages.error(request, exception.detail)
            except PermissionDenied as e:
                messages.error(request, str(e))
        else:
            messages.error(self.request, str(form.errors))
        return redirect('admission:doctorate:jury', pk=self.admission_uuid)
