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
from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from rest_framework.status import HTTP_200_OK

from admission.contrib.enums.training_choice import TrainingType, VETERINARY_BACHELOR_CODE
from admission.contrib.forms.curriculum import REQUIRED_FIELD_CLASS
from admission.tests.views.curriculum.mixin import MixinTestCase


class CreateGlobalCurriculumTestCase(MixinTestCase):
    def setUp(self):
        super().setUp()
        self.create_url = resolve_url('admission:create:curriculum')

    def test_on_create_curriculum_is_loaded(self):
        response = self.client.get(self.create_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.retrieve_curriculum_details.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertTrue(
            _("You must choose your training before filling in your previous experience."),
            response.content.decode("utf-8"),
        )


class DoctorateGlobalCurriculumTestCase(MixinTestCase):
    def setUp(self):
        super().setUp()
        self.admission_read_url = resolve_url('admission:doctorate:curriculum', pk=self.proposition.uuid)
        self.admission_update_url = resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)

    def test_with_admission_on_reading_curriculum_is_loaded(self):
        response = self.client.get(self.admission_read_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

    def test_with_admission_on_update_curriculum_is_loaded(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

        self.assertEqual(response.context.get('form').initial['curriculum'], self.proposition.curriculum)

    def test_with_admission_on_update_post_curriculum_file(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'curriculum_0': ['f1.pdf'],
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = self.mock_person_api.return_value.update_doctorat_completer_curriculum_command_admission
        update_method.assert_called_once_with(
            uuid=self.proposition.uuid,
            doctorat_completer_curriculum_command={
                'curriculum': ['f1.pdf'],
                'reponses_questions_specifiques': {},
                'uuid_proposition': self.proposition.uuid,
            },
            **self.api_default_params,
        )


class GeneralEducationGlobalCurriculumTestCase(MixinTestCase):
    def setUp(self):
        super().setUp()
        self.admission_read_url = resolve_url(
            'admission:general-education:curriculum',
            pk=self.general_proposition.uuid,
        )
        self.admission_update_url = resolve_url(
            'admission:general-education:update:curriculum',
            pk=self.general_proposition.uuid,
        )
        self.post_data = {
            'curriculum_0': ['new_file1.pdf'],
            'equivalence_diplome_0': ['new_file2.pdf'],
            'continuation_cycle_bachelier': True,
            'attestation_continuation_cycle_bachelier_0': ['new_file3.pdf'],
        }

    def test_with_admission_on_reading_curriculum_is_loaded(self):
        response = self.client.get(self.admission_read_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_general_education_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

    def test_with_admission_on_update_curriculum_is_loaded_with_master(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_general_education_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

        # Check the form
        form = response.context.get('form')
        self.assertEqual(
            form.initial['curriculum'],
            self.general_proposition.curriculum,
        )
        self.assertEqual(
            form.initial['equivalence_diplome'],
            self.general_proposition.equivalence_diplome,
        )
        self.assertEqual(
            form.initial['continuation_cycle_bachelier'],
            self.general_proposition.continuation_cycle_bachelier,
        )
        self.assertEqual(
            form.initial['attestation_continuation_cycle_bachelier'],
            self.general_proposition.attestation_continuation_cycle_bachelier,
        )

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)
        self.assertTrue(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertTrue(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_bachelor(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.BACHELOR.name
        )

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')
        self.assertEqual(
            form.initial['curriculum'],
            self.general_proposition.curriculum,
        )
        self.assertEqual(
            form.initial['equivalence_diplome'],
            self.general_proposition.equivalence_diplome,
        )
        self.assertEqual(
            form.initial['continuation_cycle_bachelier'],
            self.general_proposition.continuation_cycle_bachelier,
        )
        self.assertEqual(
            form.initial['attestation_continuation_cycle_bachelier'],
            self.general_proposition.attestation_continuation_cycle_bachelier,
        )

        self.assertTrue(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)
        self.assertFalse(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertTrue(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_veterinary_bachelor(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.BACHELOR.name
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.sigle = (
            VETERINARY_BACHELOR_CODE
        )
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')
        self.assertEqual(
            form.initial['curriculum'],
            self.general_proposition.curriculum,
        )
        self.assertEqual(
            form.initial['equivalence_diplome'],
            self.general_proposition.equivalence_diplome,
        )
        self.assertEqual(
            form.initial['continuation_cycle_bachelier'],
            self.general_proposition.continuation_cycle_bachelier,
        )
        self.assertEqual(
            form.initial['attestation_continuation_cycle_bachelier'],
            self.general_proposition.attestation_continuation_cycle_bachelier,
        )

        self.assertTrue(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)
        self.assertFalse(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertFalse(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_aggregation_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.AGGREGATION.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_general_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertFalse(form.fields['equivalence_diplome'].disabled)
        self.assertEqual(form.fields['equivalence_diplome'].widget.attrs.get('class'), REQUIRED_FIELD_CLASS)
        self.assertTrue(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertTrue(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_aggregation_and_be_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.AGGREGATION.name
        )

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)
        self.assertTrue(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertTrue(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_capes_and_be_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.CAPAES.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_general_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
            self.lite_educational_experience,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertFalse(form.fields['equivalence_diplome'].disabled)
        self.assertNotEqual(form.fields['equivalence_diplome'].widget.attrs.get('class'), REQUIRED_FIELD_CLASS)
        self.assertTrue(form.fields['continuation_cycle_bachelier'].disabled)
        self.assertTrue(form.fields['attestation_continuation_cycle_bachelier'].disabled)

    def test_with_admission_on_update_post_curriculum_file_with_master(self):
        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': [],
                'continuation_cycle_bachelier': None,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_curriculum_with_veterinary_bachelor(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.BACHELOR.name
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.sigle = (
            VETERINARY_BACHELOR_CODE
        )

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': [],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': [],
                'continuation_cycle_bachelier': True,
                'attestation_continuation_cycle_bachelier': ['new_file3.pdf'],
            },
            **self.api_default_params,
        )

        response = self.client.post(
            self.admission_update_url,
            data={
                'continuation_cycle_bachelier': False,
                'attestation_continuation_cycle_bachelier_0': ['new_file3.pdf'],
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method.assert_called_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': [],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': [],
                'continuation_cycle_bachelier': False,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_curriculum_with_bachelor(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.BACHELOR.name
        )

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': [],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': [],
                'continuation_cycle_bachelier': True,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_post_curriculum_is_loaded_with_aggregation_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.AGGREGATION.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_general_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
        ]

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': ['new_file2.pdf'],
                'continuation_cycle_bachelier': None,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_post_curriculum_is_loaded_with_aggregation_and_be_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.AGGREGATION.name
        )

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': [],
                'continuation_cycle_bachelier': None,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_post_curriculum_is_loaded_with_capes_and_be_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.formation.type = (
            TrainingType.CAPAES.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_general_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
            self.lite_educational_experience,
        ]

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_general_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            general_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.general_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.general_proposition.uuid,
                'equivalence_diplome': ['new_file2.pdf'],
                'continuation_cycle_bachelier': None,
                'attestation_continuation_cycle_bachelier': [],
            },
            **self.api_default_params,
        )


class ContinuingEducationGlobalCurriculumTestCase(MixinTestCase):
    def setUp(self):
        super().setUp()
        self.admission_read_url = resolve_url(
            'admission:continuing-education:curriculum',
            pk=self.continuing_proposition.uuid,
        )
        self.admission_update_url = resolve_url(
            'admission:continuing-education:update:curriculum',
            pk=self.continuing_proposition.uuid,
        )
        self.post_data = {
            'curriculum_0': ['new_file1.pdf'],
            'equivalence_diplome_0': ['new_file2.pdf'],
        }

    def test_with_admission_on_reading_curriculum_is_loaded(self):
        response = self.client.get(self.admission_read_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_continuing_education_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

    def test_with_admission_on_update_curriculum_is_loaded_with_certificate_of_participation(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_details_continuing_education_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

        # Check the form
        form = response.context.get('form')
        self.assertEqual(
            form.initial['curriculum'],
            self.continuing_proposition.curriculum,
        )
        self.assertEqual(
            form.initial['equivalence_diplome'],
            self.continuing_proposition.equivalence_diplome,
        )

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_first_cycle_certificate(self):
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value.formation.type = (
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
        )

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')
        self.assertEqual(
            form.initial['curriculum'],
            self.continuing_proposition.curriculum,
        )
        self.assertEqual(
            form.initial['equivalence_diplome'],
            self.continuing_proposition.equivalence_diplome,
        )

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertTrue(form.fields['equivalence_diplome'].disabled)

    def test_with_admission_on_update_curriculum_is_loaded_with_first_cycle_certificate_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value.formation.type = (
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_continuing_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.fields['curriculum'].disabled)
        self.assertFalse(form.fields['equivalence_diplome'].disabled)

    def test_with_admission_on_update_post_curriculum_file_with_certificate_of_participation(self):
        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:update:curriculum',
                pk=self.continuing_proposition.uuid,
            ),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_continuing_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.continuing_proposition.uuid,
            continuing_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.continuing_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.continuing_proposition.uuid,
                'equivalence_diplome': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_curriculum_with_first_cycle_certificate(self):
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value.formation.type = (
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
        )

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:update:curriculum',
                pk=self.continuing_proposition.uuid,
            ),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_continuing_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.continuing_proposition.uuid,
            continuing_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.continuing_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.continuing_proposition.uuid,
                'equivalence_diplome': [],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_curriculum_with_first_cycle_certificate_and_foreign_studies(self):
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value.formation.type = (
            TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
        )
        mock_return = self.mock_person_api.return_value
        mock_return.retrieve_curriculum_details_continuing_education_admission.return_value.educational_experiences = [
            self.foreign_lite_educational_experience,
        ]

        response = self.client.post(
            self.admission_update_url,
            data=self.post_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:update:curriculum',
                pk=self.continuing_proposition.uuid,
            ),
        )

        # Check that the right API calls are done
        update_method = (
            self.mock_person_api.return_value.update_continuing_education_completer_curriculum_command_admission
        )
        update_method.assert_called_once_with(
            uuid=self.continuing_proposition.uuid,
            continuing_education_completer_curriculum_command={
                'curriculum': ['new_file1.pdf'],
                'reponses_questions_specifiques': self.continuing_proposition.reponses_questions_specifiques,
                'uuid_proposition': self.continuing_proposition.uuid,
                'equivalence_diplome': ['new_file2.pdf'],
            },
            **self.api_default_params,
        )
