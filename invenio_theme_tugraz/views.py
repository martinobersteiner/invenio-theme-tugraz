# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 Graz University of Technology.
#
# invenio-theme-tugraz is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""invenio module for TUGRAZ theme."""

from functools import wraps
from typing import Dict

from flask import Blueprint, g, redirect, render_template, url_for
from flask_login import current_user, login_required
from invenio_rdm_records.proxies import current_rdm_records
from invenio_records_global_search.resources.serializers import (
    GlobalSearchJSONSerializer,
)
from invenio_users_resources.proxies import current_user_resources
from opensearch_dsl.utils import AttrDict

from .search import FrontpageRecordsSearch

blueprint = Blueprint(
    "invenio_theme_tugraz",
    __name__,
    template_folder="templates",
    static_folder="static",
)


def current_identity_is_tugraz_authenticated() -> bool:
    """Checks whether current identity has tugraz-authentication.

    NOTE: Default permission-policy has no field for `tugraz_authenticated`.
    Should the field not exist, the service checks against admin-permissions instead.
    You probably meant to configure a custom permission-policy.
    """
    rdm_service = current_rdm_records.records_service
    return rdm_service.check_permission(g.identity, "tugraz_authenticated")


def require_tugraz_authenticated(view_func):
    """Decorator for guarding view-functions against unauthenticated users.

    Redirects un-authenticated users to their personal dashboard's overview.
    """

    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not current_identity_is_tugraz_authenticated():
            return redirect(url_for("invenio_theme_tugraz.overview"))
        return view_func(*args, **kwargs)

    return decorated_view


@blueprint.route("/me/overview")
@login_required
def overview():
    """Overview."""
    url = current_user_resources.users_service.links_item_tpl.expand(
        g.identity, current_user
    )["avatar"]
    is_tugraz_authenticated = current_identity_is_tugraz_authenticated()
    return render_template(
        "invenio_theme_tugraz/overview.html",
        is_tugraz_authenticated=is_tugraz_authenticated,
        user_avatar=url,
    )


@blueprint.app_template_filter("make_dict_like")
def make_dict_like(value: str, key: str) -> Dict[str, str]:
    """Convert the value to a dict like structure.

    in the form of a key -> value pair.
    """
    return {key: value}


@blueprint.app_template_filter("cast_to_dict")
def cast_to_dict(attr_dict):
    """Return the dict structure of AttrDict variable."""
    return AttrDict.to_dict(attr_dict)


def ui_blueprint(app):
    """Blueprint for the routes and resources provided by Invenio-theme-tugraz."""
    routes = app.config.get("TUG_ROUTES")

    blueprint.add_url_rule(routes["index"], view_func=index)

    return blueprint


def records_serializer(records=None):
    """Serialize list of records."""
    serializer = GlobalSearchJSONSerializer()
    return [serializer.dump_obj(r.to_dict()) for r in records]


def index():
    """Frontpage."""
    records = FrontpageRecordsSearch()[:5].sort("-created").execute()

    return render_template(
        "invenio_theme_tugraz/index.html", records=records_serializer(records)
    )


def locked(e):
    """Error page for status locked."""
    return render_template("invenio_theme_tugraz/423.html")
