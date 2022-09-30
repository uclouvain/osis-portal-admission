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
from abc import ABC
from copy import copy
from typing import Tuple, Union

from django.forms import Form
from django.http import Http404
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import FormView

from admission.contrib.enums.training import CategorieActivite, ContexteFormation, StatutActivite
from admission.contrib.forms.training import *
from admission.contrib.views.mixins import LoadDoctorateViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.training import AdmissionDoctorateTrainingService
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException

__all__ = [
    "DoctoralTrainingListView",
    "ComplementaryTrainingListView",
    "CourseEnrollmentListView",
    "TrainingActivityAddView",
    "TrainingActivityEditView",
    "TrainingActivityDeleteView",
    "TrainingActivityAssentView",
]


class DoctoralTrainingListView(LoadDoctorateViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/training_list.html'
    form_class = BatchActivityForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['activities'] = self.activities
        context_data['statuses'] = StatutActivite.choices()
        config = AdmissionDoctorateTrainingService.get_config(person=self.person, uuid=str(self.kwargs['pk']))
        original_constants = dict(CategorieActivite.choices()).keys()
        context_data['categories'] = list(zip(original_constants, config.category_labels[get_language()]))
        return context_data

    @cached_property
    def activities(self):
        return AdmissionDoctorateTrainingService.list_doctoral_training(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )

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
        return super(WebServiceFormMixin, self).form_valid(form)


class TrainingActivityFormMixin(LoadDoctorateViewMixin, WebServiceFormMixin, FormView, ABC):
    template_name = "admission/doctorate/forms/training.html"
    form_class_mapping = {
        "doctoral-training": {
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
            CategorieActivite.COURSE: CourseForm,
            CategorieActivite.PAPER: PaperForm,
        },
        "complementary-training": {
            CategorieActivite.COURSE: ComplementaryCourseForm,
        },
        "course-enrollment": {
            CategorieActivite.UCL_COURSE: UclCourseForm,
        },
    }
    activity_uuid = None

    @property
    def namespace(self) -> str:
        """Return current url namespace, i.e.: doctoral-training, complementary-training or course-enrollment"""
        return self.request.resolver_match.namespaces[2]

    @property
    def category(self) -> str:
        """Return category being worked on"""
        return str(getattr(self, 'activity', self.kwargs).get('category')).upper()

    def get_form_class(self):
        try:
            return self.form_class_mapping[self.namespace][self.category_mapping_key]
        except KeyError as e:
            raise Http404(f"No form mapped: {e}")

    @cached_property
    def category_mapping_key(self) -> Union[Tuple[CategorieActivite, CategorieActivite], CategorieActivite]:
        """Return the form_class mapping key (with parent if needed)"""
        category = CategorieActivite[self.category]
        parent_id = getattr(self, 'activity', self.request.GET).get('parent')
        if parent_id:
            parent = AdmissionDoctorateTrainingService.retrieve_activity(
                person=self.request.user.person,
                doctorate_uuid=str(self.kwargs['pk']),
                activity_uuid=parent_id,
            )
            return CategorieActivite[str(parent.category)], category
        return category

    @cached_property
    def config(self):
        return AdmissionDoctorateTrainingService.get_config(person=self.person, uuid=str(self.kwargs['pk']))

    def get_success_url(self):
        base_url = resolve_url(':'.join(self.request.resolver_match.namespaces), pk=self.kwargs['pk'])
        return f"{base_url}#{self.activity_uuid}"

    def prepare_data(self, data):
        data = super().prepare_data(data)
        data['object_type'] = self.get_form_class().object_type

        # Get category from edited object or view kwargs
        from osis_admission_sdk.model.categorie_activite import CategorieActivite
        from osis_admission_sdk.model.contexte_formation import ContexteFormation as ContexteFormationModel

        data['category'] = CategorieActivite(self.category)

        if 'context' not in data:
            # When on a non-UCLCourseForm, context is not passed, give it current context
            data['context'] = ContexteFormationModel(
                ContexteFormation.COMPLEMENTARY_TRAINING.name
                if self.namespace == "complementary-training"
                else ContexteFormation.DOCTORAL_TRAINING.name
            )
        else:
            # When on an UCLCourseForm, context is passed, convert context
            data['context'] = ContexteFormationModel(data['context'])

        # Data cleanup and coercion
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
        kwargs['config_types'] = self.config
        kwargs['person'] = self.person
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        original_constants = dict(CategorieActivite.choices()).keys()
        context_data['categories'] = dict(zip(original_constants, self.config.category_labels[get_language()]))
        return context_data


class TrainingActivityAddView(TrainingActivityFormMixin):
    def call_webservice(self, data):
        response = AdmissionDoctorateTrainingService.create_activity(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )
        self.activity_uuid = response['uuid']


class TrainingActivityEditView(TrainingActivityFormMixin):
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'

    def get_initial(self):
        return self.activity

    @cached_property
    def activity(self):
        # breakpoint()
        return AdmissionDoctorateTrainingService.retrieve_activity(
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


class TrainingActivityDeleteView(LoadDoctorateViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/forms/training/activity_confirm_delete.html"
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'
    form_class = Form

    def call_webservice(self, data):
        AdmissionDoctorateTrainingService.delete_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
        )

    @cached_property
    def activity(self):
        return AdmissionDoctorateTrainingService.retrieve_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def get_success_url(self):
        return resolve_url(':'.join(self.request.resolver_match.namespaces), pk=self.kwargs['pk'])


class TrainingActivityAssentView(LoadDoctorateViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/forms/training/assent.html"
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'
    form_class = AssentForm

    def call_webservice(self, data):
        AdmissionDoctorateTrainingService.assent_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
            **data,
        )

    def get_initial(self):
        assent = self.activity['reference_promoter_assent']
        return {
            'approbation': True if assent is None else assent,
            'commentaire': self.activity['reference_promoter_comment'],
        }

    def get_context_data(self, **kwargs):
        kwargs['activity'] = self.activity
        return super().get_context_data(**kwargs)

    @cached_property
    def activity(self):
        return AdmissionDoctorateTrainingService.retrieve_activity(
            person=self.person,
            doctorate_uuid=str(self.kwargs['pk']),
            activity_uuid=str(self.kwargs['activity_id']),
        ).to_dict()

    def get_success_url(self):
        return resolve_url(':'.join(self.request.resolver_match.namespaces), pk=self.kwargs['pk'])


class ComplementaryTrainingListView(DoctoralTrainingListView):
    template_name = "admission/doctorate/complementary_training_list.html"

    @cached_property
    def activities(self):
        return AdmissionDoctorateTrainingService.list_complementary_training(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )


class CourseEnrollmentListView(DoctoralTrainingListView):
    template_name = "admission/doctorate/course_enrollment.html"

    @cached_property
    def activities(self):
        return AdmissionDoctorateTrainingService.list_course_enrollment(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )
