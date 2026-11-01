import sys

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

pg.setConfigOptions(antialias=True)

# Un QSlider ne manipule que des entiers : on multiplie les valeurs
# décimales par ce facteur, puis on divise en les lisant.
FACTEUR_CURSEUR = 100

# Points calculés (plus large que la zone visible : le décalage h ne laisse
# donc jamais de trou au bord du graphique).
X_MIN = -10.0
X_MAX = 10.0
NOMBRE_POINTS = 1000

# Zone visible du graphique, de -LIMITE_VISIBLE à +LIMITE_VISIBLE
LIMITE_VISIBLE = 6

# La tangente est bornée pour ne pas écraser l'échelle près des asymptotes
LIMITE_TANGENTE = 10.0

EPAISSEUR_INITIALE = 2

# Fonctions regroupées par catégorie (séparateur visuel entre les deux)
FONCTIONS_POLYNOMIALES = ["Linéaire", "Quadratique"]
FONCTIONS_TRIGONOMETRIQUES = ["Sinus", "Cosinus", "Tangente (bornée)"]

STYLE = """
QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 5px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
"""

def calculer_lineaire(x, a, h, k):
    """Calcule y = a(x - h) + k."""
    return a * (x - h) + k


def calculer_quadratique(x, a, h, k):
    """Calcule y = a(x - h)^2 + k."""
    return a * (x - h) ** 2 + k


def calculer_sinus(x, a, h, k):
    """Calcule y = a sin(x - h) + k."""
    return a * np.sin(x - h) + k


def calculer_cosinus(x, a, h, k):
    """Calcule y = a cos(x - h) + k."""
    return a * np.cos(x - h) + k


def calculer_tangente(x, a, h, k):
    """Calcule y = a tan(x - h) + k, bornée entre -10 et 10."""
    y = a * np.tan(x - h) + k
    return np.clip(y, -LIMITE_TANGENTE, LIMITE_TANGENTE)


# Pour chaque fonction : formule, fonction de calcul et bornes de chaque
# constante sous la forme (minimum, maximum, valeur par défaut).
FONCTIONS = {
    "Linéaire": {
        "formule": "y = a(x - h) + k",
        "calcul": calculer_lineaire,
        "bornes": {
            "a": (-3.0, 3.0, 1.0),
            "h": (-3.0, 3.0, 0.0),
            "k": (-3.0, 3.0, 0.0),
        },
    },
    "Quadratique": {
        "formule": "y = a(x - h)^2 + k",
        "calcul": calculer_quadratique,
        "bornes": {
            "a": (-2.0, 2.0, 1.0),
            "h": (-3.0, 3.0, 0.0),
            "k": (-3.0, 3.0, 0.0),
        },
    },
    "Sinus": {
        "formule": "y = a sin(x - h) + k",
        "calcul": calculer_sinus,
        "bornes": {
            "a": (0.2, 3.0, 1.0),
            "h": (-3.0, 3.0, 0.0),
            "k": (-3.0, 3.0, 0.0),
        },
    },
    "Cosinus": {
        "formule": "y = a cos(x - h) + k",
        "calcul": calculer_cosinus,
        "bornes": {
            "a": (0.2, 3.0, 1.0),
            "h": (-3.0, 3.0, 0.0),
            "k": (-3.0, 3.0, 0.0),
        },
    },
    "Tangente (bornée)": {
        "formule": "y = a tan(x - h) + k",
        "calcul": calculer_tangente,
        "bornes": {
            "a": (0.2, 2.0, 1.0),
            "h": (-3.0, 3.0, 0.0),
            "k": (-3.0, 3.0, 0.0),
        },
    },
}

def colorer_etiquette(etiquette: QLabel, couleur: QColor):
    """Affiche une couleur (nom hexadécimal + fond) dans une étiquette."""
    couleur_hex = couleur.name()
    # Texte blanc sur fond foncé, noir sur fond clair, pour rester lisible
    couleur_texte = "white" if couleur.lightness() < 128 else "black"
    etiquette.setText(f"Couleur : {couleur_hex}")
    etiquette.setStyleSheet(
        f"background: {couleur_hex}; color: {couleur_texte}; padding: 6px;"
    )


class FenetrePrincipale(QMainWindow):
    """Fenêtre à deux onglets : mathématiques et traitement d'images."""

    def __init__(self):
        """Construit les deux onglets, puis trace la première fonction."""
        super().__init__()
        self.setObjectName("fenetre_principale")
        self.setWindowTitle("Mini-projet 2 : fonctions et images")
        self.setStyleSheet(STYLE)

        # État de la partie 1
        self.couleur_courbe = QColor("blue")
        self.curseurs = {}
        self.etiquettes_valeurs = {}
        self.x = np.linspace(X_MIN, X_MAX, NOMBRE_POINTS)

        widget_central = QWidget()
        widget_central.setObjectName("widget_central")
        self.setCentralWidget(widget_central)
        disposition = QVBoxLayout(widget_central)

        self.onglets = QTabWidget()
        self.onglets.setObjectName("onglets")
        disposition.addWidget(self.onglets)
        self._creer_onglet_mathematiques()

        self.statusBar().showMessage("Prêt")
        self._changer_fonction()
        self._ajuster_a_l_ecran()

    def _ajuster_a_l_ecran(self):
        """Adapte la taille de la fenêtre à l'écran et la centre."""
        ecran = self.screen().availableGeometry()
        self.resize(ecran.width() * 4 // 5, ecran.height() * 4 // 5)
        cadre = self.frameGeometry()
        cadre.moveCenter(ecran.center())
        self.move(cadre.topLeft())

    def _creer_onglet_mathematiques(self):
        """Crée l'onglet 1 : graphique à gauche, contrôles à droite."""
        onglet = QWidget()
        onglet.setObjectName("onglet_mathematiques")
        ligne = QHBoxLayout(onglet)

        # Les contrôles sont créés avant le graphique : la courbe a besoin
        # de l'épaisseur choisie dans le compteur.
        colonne = QVBoxLayout()
        colonne.addWidget(self._creer_groupe_fonction())
        colonne.addWidget(self._creer_groupe_constantes())
        colonne.addWidget(self._creer_groupe_apparence())
        colonne.addStretch()

        ligne.addWidget(self._creer_graphique(), 3)
        ligne.addLayout(colonne, 1)
        self.onglets.addTab(onglet, "Mathématiques")

    def _creer_graphique(self):
        """Crée le graphique pyqtgraph (fond blanc, axes noirs) et la courbe."""
        self.zone_graphique = pg.PlotWidget()
        self.zone_graphique.setObjectName("zone_graphique")
        self.zone_graphique.setBackground("w")
        self.zone_graphique.setLabel("bottom", "x")
        self.zone_graphique.setLabel("left", "y")
        self.zone_graphique.showGrid(x=True, y=True)
        self.zone_graphique.setXRange(-LIMITE_VISIBLE, LIMITE_VISIBLE)
        self.zone_graphique.setYRange(-LIMITE_VISIBLE, LIMITE_VISIBLE)

        # Axes et texte des axes en noir
        axe_bas = self.zone_graphique.getAxis("bottom")
        axe_gauche = self.zone_graphique.getAxis("left")
        for axe in (axe_bas, axe_gauche):
            axe.setPen(pg.mkPen(color="k", width=1))
            axe.setTextPen("k")

        # La courbe est créée une seule fois : ensuite on change seulement
        # ses données (setData) ou son stylo (setPen).
        self.courbe = self.zone_graphique.plot(
            self.x, np.zeros_like(self.x), pen=self._creer_stylo()
        )
        return self.zone_graphique

    def _creer_stylo(self):
        """Crée le stylo (couleur et épaisseur) de la courbe."""
        return pg.mkPen(
            color=self.couleur_courbe,
            width=self.compteur_epaisseur.value(),
        )

    def _creer_groupe_fonction(self):
        """Crée le groupe avec la liste des fonctions et la formule."""
        groupe = QGroupBox("Fonction")
        groupe.setObjectName("groupe_fonction")
        disposition = QVBoxLayout(groupe)

        self.liste_fonctions = QComboBox()
        self.liste_fonctions.setObjectName("liste_fonctions")
        self.liste_fonctions.addItems(FONCTIONS_POLYNOMIALES)
        # Séparateur visuel entre les deux catégories
        self.liste_fonctions.insertSeparator(self.liste_fonctions.count())
        self.liste_fonctions.addItems(FONCTIONS_TRIGONOMETRIQUES)
        self.liste_fonctions.currentIndexChanged.connect(
            self._changer_fonction
        )
        disposition.addWidget(self.liste_fonctions)

        self.etiquette_formule = QLabel()
        self.etiquette_formule.setObjectName("etiquette_formule")
        self.etiquette_formule.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disposition.addWidget(self.etiquette_formule)
        return groupe

    def _creer_groupe_constantes(self):
        """Crée le groupe qui contiendra les trois curseurs a, h et k."""
        groupe = QGroupBox("Constantes")
        groupe.setObjectName("groupe_constantes")
        self.grille_curseurs = QGridLayout(groupe)
        return groupe

    def _creer_groupe_apparence(self):
        """Crée le groupe : grille, couleur et épaisseur de la courbe."""
        groupe = QGroupBox("Apparence")
        groupe.setObjectName("groupe_apparence")
        disposition = QVBoxLayout(groupe)

        self.case_grille = QCheckBox("Afficher la grille")
        self.case_grille.setObjectName("case_grille")
        self.case_grille.setChecked(True)
        self.case_grille.toggled.connect(self._basculer_grille)
        disposition.addWidget(self.case_grille)

        self.bouton_couleur = QPushButton("Choisir la couleur de la courbe")
        self.bouton_couleur.setObjectName("bouton_couleur")
        self.bouton_couleur.clicked.connect(self._choisir_couleur)
        disposition.addWidget(self.bouton_couleur)

        self.etiquette_couleur = QLabel()
        self.etiquette_couleur.setObjectName("etiquette_couleur")
        self.etiquette_couleur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colorer_etiquette(self.etiquette_couleur, self.couleur_courbe)
        disposition.addWidget(self.etiquette_couleur)

        ligne = QHBoxLayout()
        ligne.addWidget(QLabel("Épaisseur :"))
        self.compteur_epaisseur = QSpinBox()
        self.compteur_epaisseur.setObjectName("compteur_epaisseur")
        self.compteur_epaisseur.setRange(1, 4)
        self.compteur_epaisseur.setValue(EPAISSEUR_INITIALE)
        self.compteur_epaisseur.setSuffix(" px")
        self.compteur_epaisseur.valueChanged.connect(self._changer_epaisseur)
        ligne.addWidget(self.compteur_epaisseur)
        ligne.addStretch()
        disposition.addLayout(ligne)
        return groupe

    def _vider_curseurs(self):
        """Supprime les anciens curseurs et étiquettes de la grille."""
        while self.grille_curseurs.count():
            item = self.grille_curseurs.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.curseurs = {}
        self.etiquettes_valeurs = {}

    def _reconstruire_curseurs(self, nom_fonction: str):
        """Recrée les trois curseurs avec les bornes de la fonction."""
        self._vider_curseurs()
        bornes = FONCTIONS[nom_fonction]["bornes"]

        for rang, constante in enumerate(("a", "h", "k")):
            minimum, maximum, defaut = bornes[constante]

            curseur = QSlider(Qt.Orientation.Horizontal)
            curseur.setObjectName(f"curseur_{constante}")
            curseur.setRange(
                round(minimum * FACTEUR_CURSEUR),
                round(maximum * FACTEUR_CURSEUR),
            )
            curseur.setValue(round(defaut * FACTEUR_CURSEUR))
            # On connecte après setValue : pas de tracé inutile
            curseur.valueChanged.connect(self._curseur_modifie)

            etiquette_valeur = QLabel()
            etiquette_valeur.setObjectName(f"valeur_{constante}")
            etiquette_valeur.setMinimumWidth(70)

            self.curseurs[constante] = curseur
            self.etiquettes_valeurs[constante] = etiquette_valeur

            self.grille_curseurs.addWidget(QLabel(constante), rang, 0)
            self.grille_curseurs.addWidget(curseur, rang, 1)
            self.grille_curseurs.addWidget(etiquette_valeur, rang, 2)

        self._afficher_valeurs()

    def _lire_constantes(self):
        """Retourne les valeurs courantes {'a': ..., 'h': ..., 'k': ...}."""
        return {
            constante: curseur.value() / FACTEUR_CURSEUR
            for constante, curseur in self.curseurs.items()
        }

    def _afficher_valeurs(self):
        """Affiche la valeur courante de chaque curseur."""
        for constante, valeur in self._lire_constantes().items():
            self.etiquettes_valeurs[constante].setText(
                f"{constante} = {valeur:.2f}"
            )

    def _changer_fonction(self):
        """Reconstruit les curseurs et retrace pour la fonction choisie."""
        nom = self.liste_fonctions.currentText()
        self.etiquette_formule.setText(FONCTIONS[nom]["formule"])
        self._reconstruire_curseurs(nom)
        self._tracer()
        self.statusBar().showMessage(f"Fonction choisie : {nom}")

    def _curseur_modifie(self):
        """Met à jour les valeurs affichées, puis retrace immédiatement."""
        self._afficher_valeurs()
        self._tracer()

    def _tracer(self):
        """Calcule y avec les constantes courantes et met la courbe à jour."""
        nom = self.liste_fonctions.currentText()
        calcul = FONCTIONS[nom]["calcul"]
        y = calcul(self.x, **self._lire_constantes())
        self.courbe.setData(self.x, y)

    def _basculer_grille(self, coche: bool):
        """Affiche ou masque la grille du graphique."""
        self.zone_graphique.showGrid(x=coche, y=coche)

    def _choisir_couleur(self):
        """Ouvre le sélecteur de couleur et change le stylo de la courbe."""
        couleur = QColorDialog.getColor(
            self.couleur_courbe, self, "Choisir la couleur de la courbe"
        )
        if couleur.isValid():
            self.couleur_courbe = couleur
            colorer_etiquette(self.etiquette_couleur, couleur)
            # Seulement l'apparence : les données ne sont pas retracées
            self.courbe.setPen(self._creer_stylo())

    def _changer_epaisseur(self):
        """Change l'épaisseur de la courbe sans retracer les données."""
        self.courbe.setPen(self._creer_stylo())


def main():
    """Point d'entrée de l'application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    fenetre = FenetrePrincipale()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
