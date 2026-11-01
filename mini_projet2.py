import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,)

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


class FenetrePrincipale(QMainWindow):
    """Fenetre a 2 onglets: mathematiques et traitement images"""

    def __init__(self):
        """Construit les deux onglets et trace la fonction"""
        super().__init__()
        self.setObjectName("fenetre_principale")
        self.setWindowTitle("mini_projet_2:fonctions et images")
        self.setStyleSheet(STYLE)

        widget_central = QWidget()
        widget_central.setObjectName("widget_central")
        self.setCentralWidget(widget_central)
        disposition = QVBoxLayout(widget_central)

        self.onglets = QTabWidget()
        self.onglets.setObjectName("onglets")
        disposition.addWidget(self.onglets)

        self.statusBar().showMessage("pret")
        self._ajuster_a_l_ecran()

    def _ajuster_a_l_ecran(self):
        """ajuste la fenetre et la rends proportionnel a l'ecran"""
        ecran = self.screen().availableGeometry()
        self.resize(ecran.width() * 4 // 5, ecran.height() * 4 // 5)
        cadre = self.frameGeometry()
        cadre.moveCenter(ecran.center())
        self.move(cadre.topLeft())


def main():
    """Point d'entre de l'appli"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    fenetre = FenetrePrincipale()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()