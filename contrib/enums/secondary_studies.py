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
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.utils import format_academic_year
from base.models.utils.utils import ChoiceEnum


class GotDiploma(ChoiceEnum):
    YES = _("Yes")
    THIS_YEAR = _("I will be graduating from secondary school at the end of this academic year")
    NO = _("No")

    @classmethod
    def choices_with_dynamic_year(cls, current_year):
        """Return the choices with a dynamic value for the choice THIS_YEAR."""
        return tuple(
            (x.name, x.value)
            if x.name != cls.THIS_YEAR.name
            else (
                x.name,
                _("I will be graduating from secondary school during the %s academic year")
                % format_academic_year(current_year),
            )
            for x in cls
        )


HAS_DIPLOMA_CHOICES = {GotDiploma.YES.name, GotDiploma.THIS_YEAR.name}


class DiplomaTypes(ChoiceEnum):
    BELGIAN = pgettext_lazy("diploma_type", "Belgian")
    FOREIGN = pgettext_lazy("diploma_type", "foreign")


class DiplomaResults(ChoiceEnum):
    LT_65_RESULT = _("Less than 65%")
    BTW_65_AND_75_RESULT = _("Between 65 and 75%")
    GT_75_RESULT = _("More than 75%")


class BelgianCommunitiesOfEducation(ChoiceEnum):
    FRENCH_SPEAKING = _("Belgian French Community")
    FLEMISH_SPEAKING = _("Belgian Flemish Community")
    GERMAN_SPEAKING = _("German-speaking Community")


EDUCATIONAL_TYPES = (
    ("TEACHING_OF_GENERAL_EDUCATION", _('"Enseignement de formation generale"')),
    ("TRANSITION_METHOD", _('"Technique de transition"')),
    ("ARTISTIC_TRANSITION", _('"Artistique de transition"')),
    ("QUALIFICATION_METHOD", _('"Technique de qualification"')),
    ("ARTISTIC_QUALIFICATION", _('"Artistique de qualification"')),
    ("PROFESSIONAL_EDUCATION", _('"Enseignement professionnel"')),
)


# FIXME to be removed when fully replaced by EDUCATIONAL_TYPES above
class EducationalType(ChoiceEnum):
    TEACHING_OF_GENERAL_EDUCATION = _('"Enseignement de formation generale"')
    TRANSITION_METHOD = _('"Technique de transition"')
    ARTISTIC_TRANSITION = _('"Artistique de transition"')
    QUALIFICATION_METHOD = _('"Technique de qualification"')
    ARTISTIC_QUALIFICATION = _('"Artistique de qualification"')
    PROFESSIONAL_EDUCATION = _('"Enseignement professionnel"')
    PROFESSIONAL_EDUCATION_AND_MATURITY_EXAM = _("Professional education + Maturity exam")


class ForeignDiplomaTypes(ChoiceEnum):
    NATIONAL_BACHELOR = _("National baccalaureate (or state diploma, etc.)")
    EUROPEAN_BACHELOR = _("European Baccalaureate (European Schools)")
    INTERNATIONAL_BACCALAUREATE = _("International Baccalaureate (IB)")


class Equivalence(ChoiceEnum):
    YES = _("Yes")
    PENDING = _("In progress")
    NO = _("No")
