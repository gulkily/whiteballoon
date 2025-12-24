"""Invite map + new invite routes for the UI surfaces."""

from fastapi import APIRouter, Depends, Request, Response

from app.captions import build_caption_payload
from app.captions import load_preferences as load_caption_preferences
from app.dependencies import SessionDep, SessionUser, require_session_user
from app.routes.ui.helpers import describe_session_role, templates
from app.services import invite_graph_service, invite_map_cache_service

router = APIRouter(tags=["ui"])


@router.get("/invite/new")
def invite_new(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    caption_prefs = load_caption_preferences(db, session_user.user.id)
    context = {
        "request": request,
        "inviter_username": session_user.user.username,
        "session": session_user.session,
        "session_role": describe_session_role(session_user.user, session_user.session),
        "session_username": session_user.user.username,
        "session_avatar_url": session_user.avatar_url,
        "invite_caption": build_caption_payload(
            caption_prefs,
            caption_id="invite_intro",
            text="Make the invite personal so your friend lands with a smile and knows how you plan to support them.",
        ),
    }
    return templates.TemplateResponse("invite/new.html", context)


@router.get("/invite/map")
def invite_map(
    request: Request,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> Response:
    user = session_user.user
    invite_map = invite_map_cache_service.get_cached_map(db, user_id=user.id)
    cache_hit = invite_map is not None
    if not invite_map:
        invite_map = invite_graph_service.build_bidirectional_invite_map(
            db,
            root_user_id=user.id,
            max_degree=invite_graph_service.DEFAULT_MAP_DEGREE,
        )
        if invite_map:
            invite_map_cache_service.store_cached_map(db, user_id=user.id, invite_map=invite_map)

    context = {
        "request": request,
        "session": session_user.session,
        "session_role": describe_session_role(user, session_user.session),
        "session_username": user.username,
        "user": user,
        "invite_map": invite_map,
        "invite_map_cache_hit": cache_hit,
    }
    return templates.TemplateResponse("invite/map.html", context)
