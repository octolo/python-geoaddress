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

Chaque package a son propre `service.py` :

```bash
# Dans python-geoaddress/ ou django-geoaddress/
./service.py dev install-dev
./service.py dev test
./service.py quality lint
```

## Licence

MIT
