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
from django import forms
from django.utils.translation import gettext_lazy as _


class AdmissionConfirmationForm(forms.Form):
    pool = forms.CharField(widget=forms.HiddenInput())
    annee = forms.IntegerField(widget=forms.HiddenInput())


class DoctorateAdmissionConfirmationForm(AdmissionConfirmationForm):
    accept_regulations = forms.BooleanField(
        label=_(
            "In accordance with the information on the "
            "<a href='https://uclouvain.be/en/study/inscriptions/reglementations.html' target='blank'>"
            "Reglementations</a> page, "
            "I declare that I have read and accept the terms of the university regulations."
        )
    )
    accept_data_protection_policy = forms.BooleanField(
        label=_(
            "In accordance with the information on the "
            "<a href='https://uclouvain.be/en/study/inscriptions/vie-privee.html'"
            " target='blank'>Data protection policy</a> page, I declare that I have"
            " read and accept the terms of the data protection policy of the University of Louvain."
        )
    )
    accept_regulated_professions_rules = forms.BooleanField(
        label=_(
            "In accordance with the information on the "
            "<a href='https://uclouvain.be/en/study/inscriptions/acces-aux-professions-reglementees.html' "
            "target='blank'>Access to regulated professions</a> page, "
            "should it apply to me, I declare that I have received the information relating to the admission and "
            "graduation requirements and to the particular rules and restrictions of accreditation and professional "
            "establishment to which the professional or teacher training title is subject and I accept the terms."
        )
    )
    accept_max_response_time = forms.BooleanField(
        label=_(
            "The Enrolment Department reserves the right to ask you for any additional supporting documents it deems "
            "useful. This must <strong>imperatively reach us within 15 calendar days</strong>. "
            "Otherwise, your enrolment request will be closed."
        )
    )


class DoctorateAdmissionConfirmationWithBelgianDiplomaForm(DoctorateAdmissionConfirmationForm):
    accept_ucl_transfer_information_to_secondary_school = forms.BooleanField(
        label=_(
            "I authorize the UCLouvain to transmit to the secondary school in which I obtained my CESS, "
            "the information on the success."
        )
    )
