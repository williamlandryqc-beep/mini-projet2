import sys

import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
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


class FenetrePrincipale(QMainWindow):
    """Fenêtre à deux onglets : mathématiques et traitement d'images."""

    def __init__(self):
        """Construit les deux onglets, puis trace la première fonction."""
        super().__init__()
        self.setObjectName("fenetre_principale")
        self.setWindowTitle("Mini_projet_2 : fonctions et images")
        self.setStyleSheet(STYLE)

        # État de la partie 1
        self.couleur_courbe = QColor("blue")
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

        ligne.addWidget(self._creer_graphique(), 3)
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
        # Temporaire : sera lié au compteur d'épaisseur au commit 5
        return pg.mkPen(color=self.couleur_courbe, width=EPAISSEUR_INITIALE)


def main():
    """Point d'entrée de l'application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    fenetre = FenetrePrincipale()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
