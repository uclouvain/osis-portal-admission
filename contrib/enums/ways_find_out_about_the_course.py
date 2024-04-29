# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.translation import pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class ChoixMoyensDecouverteFormation(ChoiceEnum):
    SITE_WEB_UCLOUVAIN = pgettext_lazy("ways_hear_about_training", "UCLouvain website")
    SITE_FORMATION_CONTINUE = pgettext_lazy("ways_hear_about_training", "Continuing education website")
    PRESSE = pgettext_lazy("ways_hear_about_training", "In the press")
    FACEBOOK = pgettext_lazy("ways_hear_about_training", "Facebook")
    LINKEDIN = pgettext_lazy("ways_hear_about_training", "Linkedin")
    COURRIER_PERSONNALISE = pgettext_lazy("ways_hear_about_training", "Personalised mail")
    EMAILING = pgettext_lazy("ways_hear_about_training", "Email")
    BOUCHE_A_OREILLE = pgettext_lazy("ways_hear_about_training", "Word of mouth")
    AMIS = pgettext_lazy("ways_hear_about_training", "Friends")
    ANCIENS_ETUDIANTS = pgettext_lazy("ways_hear_about_training", "Former students")
    MOOCS = pgettext_lazy("ways_hear_about_training", "MOOCs")
    AUTRE = pgettext_lazy("ways_hear_about_training", "Other")
