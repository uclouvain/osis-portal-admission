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

from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class TeachingTypeEnum(ChoiceEnum):
    SOCIAL_PROMOTION = _("Social promotion")
    FULL_TIME = _("Full-time")


class Result(ChoiceEnum):
    SUCCESS = _("Success")
    SUCCESS_WITH_RESIDUAL_CREDITS = _('Success with residual credits')
    FAILURE = _('Failure')
    NO_RESULT = _('No result')


class Grade(ChoiceEnum):
    GREATER_DISTINCTION = _('Greater distinction')
    GREAT_DISTINCTION = _('Great distinction')
    DISTINCTION = _('Distinction')
    SATISFACTION = _('Satisfaction')
    SUCCESS_WITHOUT_DISTINCTION = _('Success without distinction')


class EvaluationSystem(ChoiceEnum):
    ECTS_CREDITS = _('ECTS credits')
    NON_EUROPEAN_CREDITS = _('Non-European credits')
    NO_CREDIT_SYSTEM = _('No credit system')


class TranscriptType(ChoiceEnum):
    ONE_A_YEAR = _('A transcript for each year')
    ONE_FOR_ALL_YEARS = _('A transcript for all years')


class ActivityType(ChoiceEnum):
    WORK = _('Work')
    INTERNSHIP = _('Internship')
    VOLUNTEERING = _('Volunteering')
    UNEMPLOYMENT = _('Unemployment')
    LANGUAGE_TRAVEL = _('Language travel')
    OTHER = _('Other')


class ActivitySector(ChoiceEnum):
    PRIVATE = _('Private')
    PUBLIC = _('Public')
    ASSOCIATIVE = _('Associative')


EvaluationSystemsWithCredits = {
    EvaluationSystem.ECTS_CREDITS.name,
    EvaluationSystem.NON_EUROPEAN_CREDITS.name,
}

SuccessfulResults = {
    Result.SUCCESS.name,
    Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
}
