# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.translation import gettext_lazy as _, pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class TeachingTypeEnum(ChoiceEnum):
    SOCIAL_PROMOTION = _("\"Promotion sociale\"")
    FULL_TIME = _("Full-time")


class Result(ChoiceEnum):
    SUCCESS = _("Passed")
    SUCCESS_WITH_RESIDUAL_CREDITS = _('Passed with residual credits')
    FAILURE = _('Failed')
    WAITING_RESULT = _('Waiting for a result')

    @classmethod
    def choices_for_past_years(cls):
        return tuple((x.name, x.value) for x in cls if x.name != cls.WAITING_RESULT.name)


class Grade(ChoiceEnum):
    GREATER_DISTINCTION = _('With highest honours (90-100%)')
    GREAT_DISTINCTION = _('With high honours (80-89%)')
    DISTINCTION = _('With honours (70-79%)')
    SATISFACTION = _('Satisfactory (60-69%)')
    SUCCESS_WITHOUT_DISTINCTION = _('Passed (50-59%)')


class EvaluationSystem(ChoiceEnum):
    ECTS_CREDITS = _('ECTS credits')
    NON_EUROPEAN_CREDITS = _('Non-European credits')
    NO_CREDIT_SYSTEM = _('No credit system')


class TranscriptType(ChoiceEnum):
    ONE_A_YEAR = _('A transcript for each year')
    ONE_FOR_ALL_YEARS = _('A transcript for all years')


class ActivityType(ChoiceEnum):
    WORK = _('Work')
    INTERNSHIP = pgettext_lazy('admission', 'Internship')
    VOLUNTEERING = _('Volunteering')
    UNEMPLOYMENT = _('Unemployment')
    LANGUAGE_TRAVEL = _('Language study abroad')
    OTHER = _('Other')


class ActivitySector(ChoiceEnum):
    PRIVATE = _('Private')
    PUBLIC = _('Public')
    ASSOCIATIVE = _('Non-profit')


EvaluationSystemsWithCredits = {
    EvaluationSystem.ECTS_CREDITS.name,
    EvaluationSystem.NON_EUROPEAN_CREDITS.name,
}

SuccessfulResults = {
    Result.SUCCESS.name,
    Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
}

CURRICULUM_ACTIVITY_LABEL = {
    ActivityType.LANGUAGE_TRAVEL.name: _(
        'Certificate of participation in a language study abroad for the period concerned'
    ),
    ActivityType.INTERNSHIP.name: _('Internship certificate, with dates, justifying the period concerned'),
    ActivityType.UNEMPLOYMENT.name: _(
        'Unemployment certificate issued by the relevant body, justifying the period concerned'
    ),
    ActivityType.VOLUNTEERING.name: _('Certificate, with dates, justifying your volunteering activities'),
    ActivityType.WORK.name: _('Proof of employment from the employer, with dates, justifying the period in question'),
    ActivityType.OTHER.name: _('Certificate justifying and mentioning your activity for the period concerned'),
}
