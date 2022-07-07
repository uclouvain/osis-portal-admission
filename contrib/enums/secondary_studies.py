# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _, gettext
from django.utils.functional import lazy

from base.models.utils.utils import ChoiceEnum
from base.tests.factories.academic_year import get_current_year


def get_formatted_current_year():
    current_year = get_current_year()
    return '{}-{}'.format(current_year, current_year + 1)


class GotDiploma(ChoiceEnum):
    YES = _("Yes")
    THIS_YEAR = lazy(
        lambda: gettext("I will have a high school diploma this year %s") % get_formatted_current_year(),
        str,
    )()
    NO = _("No")


HAS_DIPLOMA_CHOICES = {GotDiploma.YES.name, GotDiploma.THIS_YEAR.name}


class DiplomaTypes(ChoiceEnum):
    BELGIAN = _("belgian")
    FOREIGN = _("foreign")


class DiplomaResults(ChoiceEnum):
    LT_65_RESULT = _("Less than 65%")
    BTW_65_AND_75_RESULT = _("Between 65 and 75%")
    GT_75_RESULT = _("More than 75%")


class BelgianCommunitiesOfEducation(ChoiceEnum):
    FRENCH_SPEAKING = _("French-speaking Community")
    FLEMISH_SPEAKING = _("Flemish-speaking Community")
    GERMAN_SPEAKING = _("German-speaking Community")


EDUCATIONAL_TYPES = (
    ("TEACHING_OF_GENERAL_EDUCATION", _("Teaching of general education")),
    ("TRANSITION_METHOD", _("Transition method")),
    ("ARTISTIC_TRANSITION", _("Artistic transition")),
    ("QUALIFICATION_METHOD", _("Qualification method")),
    ("ARTISTIC_QUALIFICATION", _("Artistic qualification")),
    ("PROFESSIONAL_EDUCATION", _("Professional education")),
)


# FIXME to be removed when fully replaced by EDUCATIONAL_TYPES above
class EducationalType(ChoiceEnum):
    TEACHING_OF_GENERAL_EDUCATION = _("Teaching of general education")
    TRANSITION_METHOD = _("Transition method")
    ARTISTIC_TRANSITION = _("Artistic transition")
    QUALIFICATION_METHOD = _("Qualification method")
    ARTISTIC_QUALIFICATION = _("Artistic qualification")
    PROFESSIONAL_EDUCATION = _("Professional education")
    PROFESSIONAL_EDUCATION_AND_MATURITY_EXAM = _("Professional education + Maturity exam")


class ForeignDiplomaTypes(ChoiceEnum):
    NATIONAL_BACHELOR = _("National Bachelor (or government diploma, ...)")
    EUROPEAN_BACHELOR = _("European Bachelor (Schola Europaea)")
    INTERNATIONAL_BACCALAUREATE = _("International Baccalaureate")


class Equivalence(ChoiceEnum):
    YES = _("Yes")
    PENDING = _("Ongoing request")
    NO = _("No")
