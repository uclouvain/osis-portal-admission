# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from django.urls import reverse
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.views.generic import TemplateView

from admission.constants import (
    DOCUMENTS_REQUEST_JUST_COMPLETED_WITHOUT_DOCUMENT,
    LANGUAGE_CODE_EN,
    LANGUAGE_CODE_FR,
    PROPOSITION_JUST_SUBMITTED,
)
from admission.contrib.enums import (
    CANCELLED_STATUSES,
    IN_PROGRESS_OR_IN_PAYMENT_STATUSES,
    IN_PROGRESS_STATUSES,
    TrainingType,
)
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import TAB_TREES, can_make_action
from base.views.common import display_warning_messages

__all__ = [
    "AdmissionListView",
    "DoctorateAdmissionMemberListView",
]
__namespace__ = False


class AdmissionListView(TemplateView):
    urlpatterns = {'list': ''}
    template_name = "admission/admission_list.html"
    extra_context = {
        'LANGUAGE_CODE_FR': LANGUAGE_CODE_FR,
        'LANGUAGE_CODE_EN': LANGUAGE_CODE_EN,
        'TAB_TREES': TAB_TREES,
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = AdmissionPropositionService().get_propositions(self.request.user.person)
        context["global_links"] = result.links
        context["can_create_proposition"] = can_make_action(result, 'create_training_choice')
        context["creation_error_message"] = result.links['create_training_choice'].get('error', '')
        context['CANCELLED_STATUSES'] = CANCELLED_STATUSES
        context['just_submitted_from'] = self.request.session.pop(PROPOSITION_JUST_SUBMITTED, None)
        context['documents_request_just_completed_without_document'] = self.request.session.pop(
            DOCUMENTS_REQUEST_JUST_COMPLETED_WITHOUT_DOCUMENT,
            None,
        )
        context['candidate'] = AdmissionPersonService.retrieve_person(self.request.user.person)

        # Group and sort the propositions for display
        submitted_propositions = {}
        draft_propositions = []
        draft_or_in_payment_propositions = {}
        enrolled_or_with_submitted_proposition_trainings: set[tuple[str, int]] = set()

        for admission_context, propositions, training_field_name in [
            ('general-education', result.general_education_propositions, 'formation'),
            ('doctorate', result.doctorate_propositions, 'doctorat'),
            ('continuing-education', result.continuing_education_propositions, 'formation'),
        ]:
            for proposition in propositions:
                training = getattr(proposition, training_field_name)
                training_acronym = training.sigle
                training_year = proposition.annee_calculee or training.annee
                proposition.admission_context = admission_context
                if proposition.statut in IN_PROGRESS_OR_IN_PAYMENT_STATUSES:
                    # Group by training acronym
                    draft_or_in_payment_propositions[training_acronym] = proposition
                elif proposition.statut not in CANCELLED_STATUSES:
                    enrolled_or_with_submitted_proposition_trainings.add((training_acronym, training_year))
                if proposition.statut in IN_PROGRESS_STATUSES:
                    # Group by status
                    draft_propositions.append(proposition)
                else:
                    # Group by year
                    submitted_propositions.setdefault(training_year, []).append(proposition)

        context['draft_propositions'] = sorted(draft_propositions, key=lambda elt: elt.creee_le, reverse=True)
        context['draft_or_in_payment_propositions'] = draft_or_in_payment_propositions

        # Re-enrolment specificities
        re_enrolment_period = AdmissionPropositionService.retrieve_re_enrolment_period(self.request.user.person)

        context['ucl_enrolments_list'] = []
        context['re_enrolment_period'] = re_enrolment_period
        context['can_create_re_enrolment_proposition'] = False
        context['re_enrolment_error_message'] = ''

        if re_enrolment_period.date_debut <= datetime.date.today() <= re_enrolment_period.date_fin:
            submitted_propositions.setdefault(re_enrolment_period.annee_formation, [])

            all_ucl_enrolments_list = AdmissionPropositionService.retrieve_ucl_enrolments_list(self.request.user.person)

            re_enrolment_eligibility = AdmissionPropositionService.retrieve_candidate_re_enrolment_eligibility(
                person=self.request.user.person,
            )

            for enrolment in all_ucl_enrolments_list:
                enrolled_or_with_submitted_proposition_trainings.add((enrolment.sigle_formation, enrolment.annee))

            if re_enrolment_eligibility.est_eligible_a_la_reinscription:
                context['can_create_re_enrolment_proposition'] = context['can_create_proposition']
                context['ucl_enrolments_list'] = [
                    ucl_enrolment
                    for ucl_enrolment in all_ucl_enrolments_list
                    if ucl_enrolment.annee == re_enrolment_period.annee_formation - 1
                    and not ucl_enrolment.est_diplome
                    and ucl_enrolment.type_formation
                    not in {
                        TrainingType.PHD.name,
                        TrainingType.FORMATION_PHD.name,
                    }
                    and (
                        (ucl_enrolment.sigle_formation, re_enrolment_period.annee_formation)
                        not in enrolled_or_with_submitted_proposition_trainings
                    )
                ]

            else:
                context['re_enrolment_error_message'] = _('You have not been deliberated yet.')
                context['ucl_enrolments_list'] = [
                    ucl_enrolment
                    for ucl_enrolment in all_ucl_enrolments_list
                    if ucl_enrolment.annee == re_enrolment_period.annee_formation - 1
                    and ucl_enrolment.type_formation
                    not in {
                        TrainingType.PHD.name,
                        TrainingType.FORMATION_PHD.name,
                    }
                    and (
                        (ucl_enrolment.sigle_formation, re_enrolment_period.annee_formation)
                        not in enrolled_or_with_submitted_proposition_trainings
                    )
                ]

        # Sort submitted propositions by dates
        min_date = datetime.datetime(datetime.MINYEAR, 1, 1)
        context['submitted_propositions'] = {
            year: sorted(
                submitted_propositions[year],
                key=lambda elt: (elt.soumise_le or min_date, elt.creee_le),
                reverse=True,
            )
            for year in sorted(submitted_propositions.keys(), reverse=True)
        }

        if getattr(result, 'donnees_transferees_vers_compte_interne', False):
            msg = _(
                'Your UCLouvain account has been created. If you have not yet activated it, please '
                'follow the instructions received by email and log in with your UCLouvain account to '
                'access your registrations.'
            )
            logout_url = reverse('admission:logout')
            btn_msg = pgettext_lazy('admission', 'Logout')

            display_warning_messages(
                self.request,
                f"{str(msg)} <br>"
                f"<a href='{logout_url}' class='btn btn-sm btn-info' style='margin-top:5px;'>{str(btn_msg)}</button>",
            )

        return context


class DoctorateAdmissionMemberListView(TemplateView):
    urlpatterns = {'supervised-list': 'supervised'}
    template_name = "admission/doctorate/supervised_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admissions"] = AdmissionPropositionService().get_supervised_propositions(self.request.user.person)
        context["main_namespace"] = self.request.resolver_match.namespaces[0]
        context["tab_tree"] = TAB_TREES['doctorate']
        return context
