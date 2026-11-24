# Geoaddress

Monorepo contenant **geoaddress** (bibliothèque Python de géocodage) et **django-geoaddress** (intégration Django).

## Packages

### geoaddress — `python-geoaddress/`

Bibliothèque Python pour le géocodage et le géocodage inversé d'adresses. Interface unifiée vers plusieurs fournisseurs (Nominatim, Google Maps, Mapbox, etc.) via ProviderKit.

- **Géocodage** : adresse → coordonnées
- **Géo-inversé** : coordonnées → adresse
- **Autocomplete** : recherche d'adresses en temps réel
- **Providers gratuits** : Nominatim, Photon (sans clé API)
- **Providers payants** : Google Maps, Mapbox, LocationIQ, OpenCage, etc.

📁 Détails : [python-geoaddress/README.md](python-geoaddress/README.md) | Docs : [python-geoaddress/docs/](python-geoaddress/docs/)

### django-geoaddress — `django-geoaddress/`

Intégration Django pour Geoaddress. Champs, widgets d'autocomplete, admin.

- **GeoaddressField** : champ Django pour stocker les adresses
- **GeoaddressAutocompleteWidget** : autocomplete en temps réel
- **Admin** : gestion des adresses et providers

📁 Détails : [django-geoaddress/README.md](django-geoaddress/README.md) | Docs : [django-geoaddress/docs/](django-geoaddress/docs/)

## Structure du dépôt

```
geoaddress/
├── python-geoaddress/   # Bibliothèque core
├── django-geoaddress/   # Intégration Django
└── README.md
```

## Développement

La CI audite aussi les dépendances de chaque paquet et exécute Bandit. Les
alertes Bandit du paquet Django sont signalées sans bloquer en attendant leur
examen. Les résultats Ruff sont également signalés sans bloquer.

Chaque package a son propre `service.py` :

```bash
# Dans python-geoaddress/ ou django-geoaddress/
./service.py dev install-dev
./service.py dev test
./service.py quality lint
```

## Licence

MIT

## CI packaging check

CI also installs the built wheel(s) in a clean environment and checks their
dependencies and imports without publishing. This installation check is
non-blocking during the initial rollout.

## Local audit

Install the project's development/test dependencies (including both local
packages where applicable), plus the audit tools:

```bash
python -m pip install ruff mypy bandit pip-audit vulture radon xenon pytest pytest-django pytest-cov build twine
make audit
```

Use the activated environment's Python, or pass `make audit PYTHON=/path/to/python`.
On systems without Make, run `python scripts/audit.py` directly. Git is required;
the geoaddress widget tests also require Node.js. The audit reports missing test
suites and runs all available checks even when earlier checks fail.
Xenon checks the absolute C, module B, and average A complexity thresholds. Existing
lint, typing, security, dependency, or test findings can make the audit fail.
CI also runs this audit as a non-blocking job and separately reports Radon maintainability without imposing a threshold.
