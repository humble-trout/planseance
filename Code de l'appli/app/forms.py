from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField


#Formulaire servant à faire les filtres avancés
class FiltreFilmForm(FlaskForm):
    chaine = StringField('Titre')
    genre = SelectField('Genre', choices=[('', 'Tous')])
    annee = IntegerField('Année')

class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page if total > 0 else 1
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                #Génère les numéros de pages pour la pagination des résultats. Réalisé avec l'aide d'un LLM
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
