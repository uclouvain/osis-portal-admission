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


class ExperienceTypes(ChoiceEnum):
    BELGIAN_UNIVERSITY_HIGHER_EDUCATION = _("Belgian university higher education")
    FOREIGN_UNIVERSITY_HIGHER_EDUCATION = _("Foreign university higher education")
    OTHER = _("Other")


class BelgianCommunitiesOfEducation(ChoiceEnum):
    FRENCH_SPEAKING = _("French-speaking Community of Belgium")
    FLEMISH_SPEAKING = _("Flemish-speaking Community")
    GERMAN_SPEAKING = _("German-speaking Community")


class StudySystems(ChoiceEnum):
    CONTINUING_EDUCATION = _("Continuing education")
    FULL_TIME_EDUCATION = _("Full-time education")


class Result(ChoiceEnum):
    FAILURE = _('Failure')
    NO_RESULT = _('No result')
    SUCCESS = _("Success")
    SUCCESS_WITH_RESIDUAL_CREDITS = _('Success with residual credits')


class Grade(ChoiceEnum):
    GREATER_DISTINCTION = _('Greater distinction')
    GREAT_DISTINCTION = _('Great distinction')
    DISTINCTION = _('Distinction')
    SATISFACTION = _('Satisfaction')
    SUCCESS_WITHOUT_DISTINCTION = _('Success without distinction')
    NO_GRADE = _('No grade')


class CreditType(ChoiceEnum):
    EUROPEAN_UNION_CREDITS = _('European Union credits')
    NON_EUROPEAN_UNION_CREDITS = _('Non European Union credits')
    SEMESTERS = _('Semesters')


class ForeignStudyCycleType(ChoiceEnum):
    BACHELOR = _('Bachelor')
    DOCTORATE = _('Doctorate')
    MASTER = _('Master')
    OTHER_HIGHER_EDUCATION = _('Other higher education')


class ActivityTypes(ChoiceEnum):
    ILLNESS = _('Illness')
    INTERNSHIP = _('Internship')
    OTHER = _('Other')
    UNEMPLOYMENT = _('Unemployment')
    VOLUNTEERING = _('Volunteering')
    WORK = _('Work')
