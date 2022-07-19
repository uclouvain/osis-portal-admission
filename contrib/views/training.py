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
import re
from abc import ABC
from copy import copy

from django.http import Http404
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.contrib.enums.training import CategorieActivite, StatutActivite
from admission.contrib.forms.training import (
    BatchActivityForm,
    CommunicationForm,
    ConferenceCommunicationForm,
    ConferenceForm,
    ConferencePublicationForm,
    PublicationForm,
    ResidencyCommunicationForm,
    ResidencyForm,
    SeminarCommunicationForm,
    SeminarForm,
    ServiceForm,
    ValorisationForm,
)
from admission.contrib.views.mixins import LoadDoctorateViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionDoctorateTrainingService

__all__ = [
    "DoctorateAdmissionTrainingView",
    "DoctorateTrainingActivityAddView",
    "DoctorateTrainingActivityEditView",
]

from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException


class DoctorateAdmissionTrainingView(LoadDoctorateViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/training_list.html'
    form_class = BatchActivityForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['activities'] = self.activities
        context_data['statuses'] = StatutActivite.choices()
        context_data['categories'] = CategorieActivite.choices()
        return context_data

    @cached_property
    def activities(self):
        return AdmissionDoctorateTrainingService.get_activity_list(person=self.person, uuid=str(self.kwargs['pk']))

    def get_success_url(self):
        return self.request.get_full_path()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['uuids'] = [activity.uuid for activity in self.activities]
        return kwargs

    def prepare_data(self, data):
        return {'activity_uuids': data['activity_ids']}

    def call_webservice(self, data):
        return AdmissionDoctorateTrainingService.submit_activities(self.person, str(self.kwargs['pk']), **data)

    def form_valid(self, form):
        data = self.prepare_data(copy(form.cleaned_data))

        try:
            self.call_webservice(data)
        except MultipleApiBusinessException as multiple_business_api_exception:
            form.activities_in_error = []
            for exception in multiple_business_api_exception.exceptions:
                form.add_error(None, exception.detail)
                form.activities_in_error.append(exception.activite_id)
            return self.form_invalid(form)
        return super().form_valid(form)


class DoctorateTrainingActivityFormMixin(LoadDoctorateViewMixin, WebServiceFormMixin, FormView, ABC):
    template_name = "admission/doctorate/forms/training.html"
    permission_required = "admission.change_activity"
    form_class_mapping = {
        CategorieActivite.CONFERENCE: ConferenceForm,
        (CategorieActivite.CONFERENCE, CategorieActivite.COMMUNICATION): ConferenceCommunicationForm,
        (CategorieActivite.CONFERENCE, CategorieActivite.PUBLICATION): ConferencePublicationForm,
        CategorieActivite.RESIDENCY: ResidencyForm,
        (CategorieActivite.RESIDENCY, CategorieActivite.COMMUNICATION): ResidencyCommunicationForm,
        CategorieActivite.COMMUNICATION: CommunicationForm,
        CategorieActivite.PUBLICATION: PublicationForm,
        CategorieActivite.SERVICE: ServiceForm,
        CategorieActivite.SEMINAR: SeminarForm,
        (CategorieActivite.SEMINAR, CategorieActivite.COMMUNICATION): SeminarCommunicationForm,
        CategorieActivite.VAE: ValorisationForm,
    }
    activity_uuid = None

    def get_form_class(self):
        try:
            form_class = self.form_class_mapping[self.get_category()]
        except KeyError as e:
            raise Http404(f"No form mapped: {e}")
        return form_class

    def get_category(self):
        category = CategorieActivite[self.kwargs['category'].upper()]
        if self.request.GET.get('parent'):
            parent = AdmissionDoctorateTrainingService.get_activity(
                person=self.request.user.person,
                doctorate_uuid=str(self.kwargs['pk']),
                activity_uuid=self.request.GET.get('parent'),
            )
            return CategorieActivite[str(parent.category)], category
        return category

    def get_success_url(self):
        base_url = resolve_url("admission:doctorate:training", pk=self.kwargs['pk'])
        return f"{base_url}#{self.activity_uuid}"

    def prepare_data(self, data):
        data = super().prepare_data(data)
        pattern = re.compile("form", re.IGNORECASE)
        data['object_type'] = pattern.sub("", self.get_form_class().__name__)
        from osis_admission_sdk.model.categorie_activite import CategorieActivite

        # Get category from edited object or view kwargs
        category = getattr(self, 'activity', self.kwargs).get('category')
        data['category'] = CategorieActivite(category.upper())
        if 'parent' not in data:
            data['parent'] = self.request.GET.get('parent')
        for decimal_field in ['ects', 'participating_days']:
            if decimal_field in data:
                if not data[decimal_field]:
                    data[decimal_field] = 0.0
                else:
                    data[decimal_field] = float(data[decimal_field])
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['config_types'] = AdmissionDoctorateTrainingService.get_config(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )
        return kwargs


class DoctorateTrainingActivityAddView(DoctorateTrainingActivityFormMixin):
    def call_webservice(self, data):
        response = AdmissionDoctorateTrainingService.create_activity(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )
        self.activity_uuid = response['uuid']


class DoctorateTrainingActivityEditView(DoctorateTrainingActivityFormMixin):
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'

    def get_category(self):
        category = CategorieActivite[self.activity['category']]
        if self.activity.get('parent'):
            parent = AdmissionDoctorateTrainingService.get_activity(
                person=self.person,
                doctorate_uuid=str(self.kwargs['pk']),
                activity_uuid=self.activity['parent'],
            )
            return CategorieActivite[str(parent.category)], category
        return category

    def get_initial(self):
        return self.activity

    @cached_property
    def activity(self):
        return AdmissionDoctorateTrainingService.get_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def prepare_data(self, data):
        data['category'] = self.activity['category']
        data['parent'] = self.activity.get('parent')
        return super().prepare_data(data)

    def call_webservice(self, data):
        response = AdmissionDoctorateTrainingService.update_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
            **data,
        )
        self.activity_uuid = response['uuid']
