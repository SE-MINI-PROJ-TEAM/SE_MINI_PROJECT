"""Feature auto-discovery.

Every sub-package of ``app.features`` implements one user story. A package participates by exposing a Flask
``Blueprint`` named ``bp`` in its ``__init__.py``. Packages are discovered at start-up, so a story can be added
(or removed) by dropping its folder in / out without editing any shared file.
"""
import importlib
import pkgutil

API_PREFIX = "/api/v1"


def register_features(app):
    loaded = []
    for module_info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if not module_info.ispkg:
            continue
        module = importlib.import_module(f"{__name__}.{module_info.name}")
        blueprint = getattr(module, "bp", None)
        if blueprint is not None:
            app.register_blueprint(blueprint, url_prefix=API_PREFIX)
            loaded.append(module_info.name)
    app.config["LOADED_FEATURES"] = loaded
    return loaded
